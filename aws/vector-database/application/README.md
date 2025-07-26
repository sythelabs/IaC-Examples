# Vector Database Application

This directory contains the **application logic** for the vector database, properly separated from the infrastructure code.

## 🏗️ Architecture

```
application/
├── src/                    # Core application code
│   ├── vector_service.py   # Business logic for vector operations
│   ├── api_handler.py      # HTTP request handling
│   └── __init__.py
├── tests/                  # Unit tests
│   ├── test_vector_service.py
│   └── requirements.txt
├── lambda_handler.py       # Lambda entry point
├── requirements.txt        # Application dependencies
└── README.md              # This file
```

## 🎯 Separation of Concerns

### Infrastructure (CDK Stack)

- **What**: AWS resources, networking, security, scaling
- **Where**: `../lib/vector-database-stack.ts`
- **Responsibility**: Deploy and manage AWS services

### Application (This Directory)

- **What**: Business logic, data models, API handling
- **Where**: `application/` directory
- **Responsibility**: Vector operations, data processing, request handling

## 🔧 Core Components

### 1. Vector Service (`src/vector_service.py`)

**Business Logic Layer**

- `VectorData` - Data model for vector storage
- `SearchQuery` - Data model for search requests
- `VectorService` - Main service orchestrator
- `OpenSearchVectorRepository` - Vector storage implementation
- `MetadataRepository` - Metadata storage implementation

### 2. API Handler (`src/api_handler.py`)

**HTTP Request Layer**

- `APIHandler` - Handles HTTP requests/responses
- Request validation and error handling
- Delegates to VectorService for business logic

### 3. Lambda Handler (`lambda_handler.py`)

**Entry Point**

- Minimal Lambda function entry point
- Configuration setup
- Delegates to APIHandler

## 🧪 Testing

### Running Tests

```bash
cd application
pip install -r tests/requirements.txt
pytest tests/
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Mocked Dependencies**: No external service calls
- **Data Model Validation**: Pydantic model testing
- **Error Handling**: Exception scenarios

## 📦 Dependencies

### Core Dependencies

- `opensearch-py` - OpenSearch client
- `psycopg2-binary` - PostgreSQL client
- `requests-aws4auth` - AWS authentication
- `pydantic` - Data validation
- `boto3` - AWS SDK

### Development Dependencies

- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities

## 🚀 Development Workflow

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run linting
flake8 src/
```

### 2. Application Changes

1. Modify business logic in `src/vector_service.py`
2. Update API handling in `src/api_handler.py`
3. Add tests in `tests/`
4. Test locally
5. Deploy via CDK

### 3. Deployment

```bash
# From project root
./deploy.sh
```

## 🎨 Design Patterns

### Repository Pattern

- Abstract `VectorRepository` interface
- Concrete `OpenSearchVectorRepository` implementation
- Easy to swap storage backends

### Service Layer Pattern

- `VectorService` orchestrates operations
- Separates business logic from data access
- Enables transaction management

### Dependency Injection

- Configuration passed to services
- Easy to test with mocks
- Loose coupling between components

## 🔒 Security

### Data Validation

- Pydantic models validate all inputs
- Type checking and constraint validation
- Prevents injection attacks

### Error Handling

- Comprehensive exception handling
- No sensitive data in error messages
- Proper logging for debugging

### AWS Integration

- IAM roles for service access
- Secrets Manager for credentials
- VPC isolation for databases

## 📈 Scalability

### Horizontal Scaling

- Stateless Lambda functions
- Auto-scaling based on demand
- No shared state between instances

### Performance

- Connection pooling for databases
- Efficient vector search algorithms
- Optimized data models

## 🔄 Future Enhancements

### Potential Improvements

1. **Caching Layer**: Redis for frequently accessed data
2. **Batch Operations**: Bulk vector storage/search
3. **Streaming**: Real-time vector updates
4. **Analytics**: Usage metrics and monitoring
5. **Multi-tenancy**: Support for multiple customers

### Alternative Storage

1. **pgvector**: PostgreSQL vector extension
2. **Pinecone**: Managed vector database
3. **Weaviate**: Vector search engine
4. **Qdrant**: Vector similarity search

## 📚 Best Practices

### Code Organization

- Single responsibility principle
- Clear separation of concerns
- Comprehensive error handling
- Extensive unit testing

### AWS Best Practices

- Least privilege IAM policies
- VPC isolation
- Encryption at rest and in transit
- Proper logging and monitoring

### Python Best Practices

- Type hints throughout
- Pydantic for data validation
- Comprehensive docstrings
- PEP 8 code style
