"""
API Handler for Lambda Function
Thin layer that handles HTTP requests and delegates to the vector service
"""

import json
import logging
from typing import Dict, Any
from http import HTTPStatus

from .vector_service import VectorService, DatabaseConfig, VectorData, SearchQuery

# Configure logging
logger = logging.getLogger(__name__)


class APIHandler:
    """Handles HTTP API requests for vector operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.vector_service = VectorService(config)
    
    def handle_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Main request handler"""
        try:
            http_method = event.get('httpMethod', 'GET')
            
            if http_method == 'POST':
                return self._handle_post_request(event)
            elif http_method == 'GET':
                return self._handle_get_request(event)
            else:
                return self._create_response(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    {'error': f'Method {http_method} not allowed'}
                )
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._create_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {'error': 'Internal server error'}
            )
    
    def _handle_post_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST requests for storing vectors"""
        try:
            body = json.loads(event.get('body', '{}'))
            
            if 'id' not in body or 'vector' not in body:
                return self._create_response(
                    HTTPStatus.BAD_REQUEST,
                    {'error': 'Missing required fields: id and vector'}
                )
            
            # Create vector data object
            vector_data = VectorData(
                id=body['id'],
                vector=body['vector'],
                metadata=body.get('metadata', {})
            )
            
            # Store the vector
            success = self.vector_service.store_vector(vector_data)
            
            if success:
                return self._create_response(
                    HTTPStatus.OK,
                    {
                        'message': 'Vector stored successfully',
                        'id': vector_data.id
                    }
                )
            else:
                return self._create_response(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {'error': 'Failed to store vector'}
                )
                
        except json.JSONDecodeError:
            return self._create_response(
                HTTPStatus.BAD_REQUEST,
                {'error': 'Invalid JSON in request body'}
            )
        except Exception as e:
            logger.error(f"Error in POST request: {e}")
            return self._create_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {'error': 'Internal server error'}
            )
    
    def _handle_get_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GET requests for searching vectors"""
        try:
            query_params = event.get('queryStringParameters', {})
            
            if 'vector' not in query_params:
                return self._create_response(
                    HTTPStatus.BAD_REQUEST,
                    {'error': 'Missing required parameter: vector'}
                )
            
            # Parse query parameters
            try:
                query_vector = json.loads(query_params['vector'])
                k = int(query_params.get('k', '10'))
            except (json.JSONDecodeError, ValueError):
                return self._create_response(
                    HTTPStatus.BAD_REQUEST,
                    {'error': 'Invalid vector format or k parameter'}
                )
            
            # Create search query
            search_query = SearchQuery(vector=query_vector, k=k)
            
            # Perform search
            results = self.vector_service.search_vectors(search_query)
            
            serializable_results = [
                {
                    'id': result.id,
                    'score': result.score,
                    'metadata': result.metadata
                }
                for result in results
            ]
            
            return self._create_response(
                HTTPStatus.OK,
                {'results': serializable_results}
            )
            
        except Exception as e:
            logger.error(f"Error in GET request: {e}")
            return self._create_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {'error': 'Internal server error'}
            )
    
    def _create_response(self, status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized API response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps(body)
        }


def create_handler(config: DatabaseConfig):
    """Factory function to create an API handler"""
    return APIHandler(config) 