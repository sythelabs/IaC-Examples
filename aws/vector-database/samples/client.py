#!/usr/bin/env python3
"""
Sample client for the Vector Database API
This script demonstrates how to interact with the deployed vector database.
"""

import requests
import json
import numpy as np
from typing import List, Dict, Any
import time

class VectorDatabaseClient:
    def __init__(self, api_url: str):
        """
        Initialize the vector database client.
        
        Args:
            api_url: The base URL of the Vector Database API
        """
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def store_vector(self, vector_id: str, vector: List[float], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a vector with its metadata.
        
        Args:
            vector_id: Unique identifier for the vector
            vector: The vector as a list of floats
            metadata: Optional metadata dictionary
            
        Returns:
            API response as dictionary
        """
        payload = {
            'id': vector_id,
            'vector': vector,
            'metadata': metadata or {}
        }
        
        response = self.session.post(f"{self.api_url}/vectors", json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_vectors(self, query_vector: List[float], k: int = 10) -> Dict[str, Any]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: The query vector as a list of floats
            k: Number of results to return
            
        Returns:
            API response with search results
        """
        params = {
            'vector': json.dumps(query_vector),
            'k': k
        }
        
        response = self.session.get(f"{self.api_url}/vectors", params=params)
        response.raise_for_status()
        return response.json()
    
    def batch_store_vectors(self, vectors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Store multiple vectors in batch.
        
        Args:
            vectors_data: List of dictionaries with 'id', 'vector', and 'metadata' keys
            
        Returns:
            List of API responses
        """
        responses = []
        for data in vectors_data:
            try:
                response = self.store_vector(
                    data['id'],
                    data['vector'],
                    data.get('metadata', {})
                )
                responses.append(response)
                print(f"Stored vector: {data['id']}")
            except Exception as e:
                print(f"Error storing vector {data['id']}: {e}")
                responses.append({'error': str(e)})
        
        return responses

def generate_sample_vectors(num_vectors: int = 100, dimension: int = 1536) -> List[Dict[str, Any]]:
    """
    Generate sample vectors for testing.
    
    Args:
        num_vectors: Number of vectors to generate
        dimension: Dimension of each vector
        
    Returns:
        List of vector data dictionaries
    """
    vectors = []
    for i in range(num_vectors):
        # Generate random vector
        vector = np.random.normal(0, 1, dimension).tolist()
        
        # Normalize the vector
        norm = np.linalg.norm(vector)
        vector = [x / norm for x in vector]
        
        # Create metadata
        metadata = {
            'title': f'Sample Document {i+1}',
            'category': np.random.choice(['technology', 'science', 'art', 'history']),
            'tags': np.random.choice(['ai', 'ml', 'data', 'research', 'innovation'], 
                                   size=np.random.randint(1, 4), replace=False).tolist(),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'vector_id': f'vector_{i+1:04d}'
        }
        
        vectors.append({
            'id': f'vector_{i+1:04d}',
            'vector': vector,
            'metadata': metadata
        })
    
    return vectors

def main():
    """
    Main function demonstrating the vector database usage.
    """
    # Replace with your actual API Gateway URL
    API_URL = "https://your-api-gateway-url.amazonaws.com/prod"
    
    # Initialize client
    client = VectorDatabaseClient(API_URL)
    
    print("🚀 Vector Database Client Demo")
    print("=" * 50)
    
    # Generate sample vectors
    print("📊 Generating sample vectors...")
    sample_vectors = generate_sample_vectors(num_vectors=50, dimension=1536)
    
    # Store vectors
    print("💾 Storing vectors in the database...")
    responses = client.batch_store_vectors(sample_vectors)
    
    # Wait a moment for indexing
    print("⏳ Waiting for indexing to complete...")
    time.sleep(5)
    
    # Perform some searches
    print("🔍 Performing similarity searches...")
    
    # Search with the first vector
    query_vector = sample_vectors[0]['vector']
    results = client.search_vectors(query_vector, k=5)
    
    print("\n📈 Search Results:")
    print(f"Query vector: {sample_vectors[0]['id']}")
    print(f"Found {len(results['results'])} similar vectors:")
    
    for i, result in enumerate(results['results'], 1):
        print(f"{i}. ID: {result['id']}, Score: {result['score']:.4f}")
        print(f"   Title: {result['metadata'].get('title', 'N/A')}")
        print(f"   Category: {result['metadata'].get('category', 'N/A')}")
    
    # Search with a random vector
    print("🎲 Searching with a random vector...")
    random_vector = np.random.normal(0, 1, 1536).tolist()
    norm = np.linalg.norm(random_vector)
    random_vector = [x / norm for x in random_vector]
    
    results = client.search_vectors(random_vector, k=3)
    
    print(f"Found {len(results['results'])} similar vectors:")
    for i, result in enumerate(results['results'], 1):
        print(f"{i}. ID: {result['id']}, Score: {result['score']:.4f}")
        print(f"   Title: {result['metadata'].get('title', 'N/A')}")
        print()

if __name__ == "__main__":
    main() 