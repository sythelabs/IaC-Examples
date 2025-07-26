"""
Unit tests for Vector Service
"""

import pytest
from unittest.mock import Mock, patch
from src.vector_service import (
    VectorData, 
    SearchQuery, 
    SearchResult, 
    DatabaseConfig,
    VectorService,
    OpenSearchVectorRepository,
    MetadataRepository
)


class TestVectorData:
    """Test VectorData model"""
    
    def test_vector_data_creation(self):
        """Test creating VectorData with valid data"""
        vector_data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3],
            metadata={"title": "Test Document"}
        )
        
        assert vector_data.id == "test_id"
        assert vector_data.vector == [0.1, 0.2, 0.3]
        assert vector_data.metadata["title"] == "Test Document"
    
    def test_vector_data_default_metadata(self):
        """Test VectorData with default metadata"""
        vector_data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3]
        )
        
        assert vector_data.metadata == {}


class TestSearchQuery:
    """Test SearchQuery model"""
    
    def test_search_query_creation(self):
        """Test creating SearchQuery with valid data"""
        query = SearchQuery(
            vector=[0.1, 0.2, 0.3],
            k=5
        )
        
        assert query.vector == [0.1, 0.2, 0.3]
        assert query.k == 5
    
    def test_search_query_default_k(self):
        """Test SearchQuery with default k value"""
        query = SearchQuery(vector=[0.1, 0.2, 0.3])
        
        assert query.k == 10


class TestVectorService:
    """Test VectorService integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock database configuration"""
        return DatabaseConfig(
            opensearch_endpoint="https://test-opensearch.amazonaws.com",
            rds_endpoint="test-cluster.amazonaws.com",
            rds_secret_arn="arn:aws:secretsmanager:region:account:secret:test",
            aws_region="us-east-1"
        )
    
    @patch('src.vector_service.OpenSearchVectorRepository')
    @patch('src.vector_service.MetadataRepository')
    def test_store_vector_success(self, mock_metadata_repo, mock_vector_repo, mock_config):
        """Test successful vector storage"""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_vector_instance.store_vector.return_value = True
        mock_vector_repo.return_value = mock_vector_instance
        
        mock_metadata_instance = Mock()
        mock_metadata_instance.store_metadata.return_value = True
        mock_metadata_repo.return_value = mock_metadata_instance
        
        # Create service
        service = VectorService(mock_config)
        
        # Test data
        vector_data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3],
            metadata={"title": "Test"}
        )
        
        # Execute
        result = service.store_vector(vector_data)
        
        # Assert
        assert result is True
        mock_vector_instance.store_vector.assert_called_once_with(vector_data)
        mock_metadata_instance.store_metadata.assert_called_once_with(
            "test_id", {"title": "Test"}
        )
    
    @patch('src.vector_service.OpenSearchVectorRepository')
    @patch('src.vector_service.MetadataRepository')
    def test_store_vector_failure(self, mock_metadata_repo, mock_vector_repo, mock_config):
        """Test vector storage failure"""
        # Setup mocks
        mock_vector_instance = Mock()
        mock_vector_instance.store_vector.return_value = False
        mock_vector_repo.return_value = mock_vector_instance
        
        mock_metadata_instance = Mock()
        mock_metadata_repo.return_value = mock_metadata_instance
        
        # Create service
        service = VectorService(mock_config)
        
        # Test data
        vector_data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3]
        )
        
        # Execute
        result = service.store_vector(vector_data)
        
        # Assert
        assert result is False
        mock_vector_instance.store_vector.assert_called_once_with(vector_data)
        # Metadata should not be called if vector storage fails
        mock_metadata_instance.store_metadata.assert_not_called()
    
    @patch('src.vector_service.OpenSearchVectorRepository')
    @patch('src.vector_service.MetadataRepository')
    def test_search_vectors(self, mock_metadata_repo, mock_vector_repo, mock_config):
        """Test vector search"""
        # Setup mocks
        mock_vector_instance = Mock()
        expected_results = [
            SearchResult(id="1", score=0.95, metadata={"title": "Doc 1"}),
            SearchResult(id="2", score=0.85, metadata={"title": "Doc 2"})
        ]
        mock_vector_instance.search_vectors.return_value = expected_results
        mock_vector_repo.return_value = mock_vector_instance
        
        mock_metadata_instance = Mock()
        mock_metadata_repo.return_value = mock_metadata_instance
        
        # Create service
        service = VectorService(mock_config)
        
        # Test data
        query = SearchQuery(vector=[0.1, 0.2, 0.3], k=5)
        
        # Execute
        results = service.search_vectors(query)
        
        # Assert
        assert results == expected_results
        mock_vector_instance.search_vectors.assert_called_once_with(query)


class TestOpenSearchVectorRepository:
    """Test OpenSearch repository"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock database configuration"""
        return DatabaseConfig(
            opensearch_endpoint="https://test-opensearch.amazonaws.com",
            rds_endpoint="test-cluster.amazonaws.com",
            rds_secret_arn="arn:aws:secretsmanager:region:account:secret:test",
            aws_region="us-east-1"
        )
    
    @patch('src.vector_service.OpenSearch')
    @patch('src.vector_service.AWS4Auth')
    @patch('boto3.Session')
    def test_create_opensearch_client(self, mock_session, mock_aws4auth, mock_opensearch, mock_config):
        """Test OpenSearch client creation"""
        # Setup mocks
        mock_credentials = Mock()
        mock_credentials.access_key = "test_key"
        mock_credentials.secret_key = "test_secret"
        mock_credentials.token = "test_token"
        mock_session.return_value.get_credentials.return_value = mock_credentials
        
        mock_auth = Mock()
        mock_aws4auth.return_value = mock_auth
        
        mock_client = Mock()
        mock_opensearch.return_value = mock_client
        
        # Execute
        repo = OpenSearchVectorRepository(mock_config)
        
        # Assert
        assert repo.client == mock_client
        mock_opensearch.assert_called_once()
        mock_aws4auth.assert_called_once_with(
            "test_key", "test_secret", "us-east-1", "es", session_token="test_token"
        )


class TestMetadataRepository:
    """Test Metadata repository"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock database configuration"""
        return DatabaseConfig(
            opensearch_endpoint="https://test-opensearch.amazonaws.com",
            rds_endpoint="test-cluster.amazonaws.com",
            rds_secret_arn="arn:aws:secretsmanager:region:account:secret:test",
            aws_region="us-east-1"
        )
    
    @patch('src.vector_service.psycopg2.connect')
    @patch('boto3.client')
    def test_store_metadata_success(self, mock_boto_client, mock_psycopg2, mock_config):
        """Test successful metadata storage"""
        # Setup mocks
        mock_secrets_client = Mock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': '{"username": "test", "password": "test"}'
        }
        mock_boto_client.return_value = mock_secrets_client
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection
        mock_psycopg2.return_value = mock_connection
        
        # Create repository
        repo = MetadataRepository(mock_config)
        
        # Execute
        result = repo.store_metadata("test_id", {"title": "Test"})
        
        # Assert
        assert result is True
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called() 