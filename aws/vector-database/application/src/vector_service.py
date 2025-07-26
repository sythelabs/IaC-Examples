"""
Vector Database Service
Core business logic for vector operations
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

import boto3
import psycopg2
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorData(BaseModel):
    """Data model for vector storage"""
    id: str = Field(..., description="Unique identifier for the vector")
    vector: List[float] = Field(..., description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated metadata")


class SearchResult(BaseModel):
    """Data model for search results"""
    id: str
    score: float
    metadata: Dict[str, Any]


class SearchQuery(BaseModel):
    """Data model for search queries"""
    vector: List[float]
    k: int = Field(default=10, ge=1, le=100)


@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    opensearch_endpoint: str
    rds_endpoint: str
    rds_secret_arn: str
    aws_region: str


class VectorRepository(ABC):
    """Abstract base class for vector storage operations"""
    
    @abstractmethod
    def store_vector(self, vector_data: VectorData) -> bool:
        """Store a vector with metadata"""
        pass
    
    @abstractmethod
    def search_vectors(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    def get_vector(self, vector_id: str) -> Optional[VectorData]:
        """Retrieve a specific vector"""
        pass


class OpenSearchVectorRepository(VectorRepository):
    """OpenSearch implementation of vector storage"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = self._create_opensearch_client()
        self._ensure_index_exists()
    
    def _create_opensearch_client(self) -> OpenSearch:
        """Create OpenSearch client with AWS authentication"""
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.config.aws_region,
            'es',
            session_token=credentials.token
        )
        
        return OpenSearch(
            hosts=[{'host': self.config.opensearch_endpoint.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
    
    def _ensure_index_exists(self):
        """Ensure the vectors index exists with proper mapping"""
        try:
            if not self.client.indices.exists(index='vectors'):
                mapping = {
                    "mappings": {
                        "properties": {
                            "vector": {
                                "type": "knn_vector",
                                "dimension": 1536,
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "nmslib"
                                }
                            },
                            "metadata": {
                                "type": "object"
                            }
                        }
                    }
                }
                self.client.indices.create(index='vectors', body=mapping)
                logger.info("Created vectors index with k-NN mapping")
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise
    
    def store_vector(self, vector_data: VectorData) -> bool:
        """Store a vector in OpenSearch"""
        try:
            self.client.index(
                index='vectors',
                id=vector_data.id,
                body={
                    'vector': vector_data.vector,
                    'metadata': vector_data.metadata
                }
            )
            logger.info(f"Stored vector: {vector_data.id}")
            return True
        except Exception as e:
            logger.error(f"Error storing vector {vector_data.id}: {e}")
            return False
    
    def search_vectors(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar vectors using k-NN"""
        try:
            search_body = {
                'size': query.k,
                'query': {
                    'knn': {
                        'vector': {
                            'vector': query.vector,
                            'k': query.k
                        }
                    }
                }
            }
            
            response = self.client.search(index='vectors', body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                results.append(SearchResult(
                    id=hit['_id'],
                    score=hit['_score'],
                    metadata=hit['_source'].get('metadata', {})
                ))
            
            logger.info(f"Found {len(results)} similar vectors")
            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def get_vector(self, vector_id: str) -> Optional[VectorData]:
        """Retrieve a specific vector"""
        try:
            response = self.client.get(index='vectors', id=vector_id)
            source = response['_source']
            return VectorData(
                id=vector_id,
                vector=source['vector'],
                metadata=source.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error retrieving vector {vector_id}: {e}")
            return None


class MetadataRepository:
    """Repository for metadata storage in PostgreSQL"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._ensure_table_exists()
    
    def _get_connection(self):
        """Get database connection"""
        rds_secret = boto3.client('secretsmanager').get_secret_value(
            SecretId=self.config.rds_secret_arn
        )
        db_creds = json.loads(rds_secret['SecretString'])
        
        return psycopg2.connect(
            host=self.config.rds_endpoint,
            database='postgres',
            user=db_creds['username'],
            password=db_creds['password']
        )
    
    def _ensure_table_exists(self):
        """Ensure the metadata table exists"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS vector_metadata (
                            id VARCHAR(255) PRIMARY KEY,
                            metadata JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_vector_metadata_created_at 
                        ON vector_metadata(created_at);
                        
                        CREATE INDEX IF NOT EXISTS idx_vector_metadata_updated_at 
                        ON vector_metadata(updated_at);
                    """)
                    conn.commit()
                    logger.info("Ensured metadata table exists")
        except Exception as e:
            logger.error(f"Error ensuring table exists: {e}")
            raise
    
    def store_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """Store metadata in PostgreSQL"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO vector_metadata (id, metadata, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (id) DO UPDATE SET
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """, (vector_id, json.dumps(metadata)))
                    conn.commit()
                    logger.info(f"Stored metadata for vector: {vector_id}")
                    return True
        except Exception as e:
            logger.error(f"Error storing metadata for {vector_id}: {e}")
            return False
    
    def get_metadata(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata from PostgreSQL"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT metadata FROM vector_metadata WHERE id = %s
                    """, (vector_id,))
                    result = cur.fetchone()
                    if result:
                        return json.loads(result[0])
                    return None
        except Exception as e:
            logger.error(f"Error retrieving metadata for {vector_id}: {e}")
            return None


class VectorService:
    """Main service class that orchestrates vector operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.vector_repo = OpenSearchVectorRepository(config)
        self.metadata_repo = MetadataRepository(config)
    
    def store_vector(self, vector_data: VectorData) -> bool:
        """Store a vector with metadata"""
        # Store vector in OpenSearch
        vector_success = self.vector_repo.store_vector(vector_data)
        
        # Store metadata in PostgreSQL
        metadata_success = self.metadata_repo.store_metadata(
            vector_data.id, 
            vector_data.metadata
        )
        
        return vector_success and metadata_success
    
    def search_vectors(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar vectors"""
        return self.vector_repo.search_vectors(query)
    
    def get_vector(self, vector_id: str) -> Optional[VectorData]:
        """Retrieve a vector with its metadata"""
        vector_data = self.vector_repo.get_vector(vector_id)
        if vector_data:
            # Optionally enrich with additional metadata from PostgreSQL
            additional_metadata = self.metadata_repo.get_metadata(vector_id)
            if additional_metadata:
                vector_data.metadata.update(additional_metadata)
        return vector_data 