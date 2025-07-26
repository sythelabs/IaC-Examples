# Vector Database Infrastructure with AWS CDK v2

A complete vector database infrastructure on AWS using OpenSearch for vector search and Aurora PostgreSQL for metadata storage.

## Architecture

```
API Gateway → Lambda Function → OpenSearch + Aurora PostgreSQL
```

### Infrastructure (CDK)

- **OpenSearch Domain** - Vector similarity search with k-NN
- **Aurora PostgreSQL** - Metadata storage
- **Lambda Function** - Serverless API backend
- **API Gateway** - REST API endpoints
- **VPC** - Network isolation
- **S3 Bucket** - Object storage

### Application (Python)

- **Vector Service** - Business logic
- **Repository Pattern** - Data access layer
- **API Handler** - HTTP request handling
- **Unit Tests** - Test coverage

## Prerequisites

- Node.js 18+
- AWS CLI configured
- AWS CDK CLI: `npm install -g aws-cdk`

## Quick Start

```bash
# Install dependencies
npm install

# Deploy infrastructure
./deploy.sh
```

## What Gets Deployed

### Core Resources

- **VPC** with public/private subnets
- **OpenSearch Domain** (2 t3.small.search nodes, 20GB each)
- **Aurora PostgreSQL** (2 db.t3.micro instances)
- **Lambda Function** (Python 3.11, 512MB, 30s timeout)
- **API Gateway** with CORS enabled
- **S3 Bucket** for data storage
- **Secrets Manager** for database credentials

### API Endpoints

- `POST /vectors` - Store vector with metadata
- `GET /vectors?vector=[...]&k=10` - Search similar vectors

## Required Customization

### 1. AWS Configuration (`bin/vector-database.ts`)

```typescript
new VectorDatabaseStack(app, "VectorDatabaseStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
})
```

### 2. Resource Names (`lib/vector-database-stack.ts`)

```typescript
// Change these to be unique
openSearchDomainName: "my-vector-search-domain",
auroraClusterIdentifier: "my-vector-cluster",
```

### 3. Vector Dimensions (`application/src/vector_service.py`)

```python
"dimension": 1536,  # Change to match your vector size
```

### 4. Production Settings

```typescript
// Remove demo settings for production
removalPolicy: cdk.RemovalPolicy.RETAIN,
autoDeleteObjects: false,
deletionProtection: true,
```

## Estimated Cost (us-east-1)

- **OpenSearch**: ~$60/month
- **Aurora**: ~$40/month
- **VPC/NAT**: ~$45/month
- **Lambda/API Gateway**: ~$10/month
- **Total**: ~$155/month

## Testing

```bash
# Update API URL in samples/client.py
API_URL = "https://your-api-gateway-url.amazonaws.com/prod/"

# Run test client
cd samples && pip install -r requirements.txt && python client.py
```

## Useful Commands

```bash
# Deploy
./deploy.sh

# Destroy
npm run destroy

# Check changes
npm run diff

# Run tests
cd application && pytest tests/
```

## Troubleshooting

### Common Issues

- **VPC limits**: Delete unused VPCs or request increase
- **Instance limits**: Request increase or use smaller instances
- **Domain name exists**: Change `openSearchDomainName`
- **Cluster exists**: Change `auroraClusterIdentifier`

### Debug Commands

```bash
# Check deployment
cdk diff

# View logs
aws logs tail /aws/lambda/VectorOperationsFunction --follow

# Test function
aws lambda invoke --function-name VectorOperationsFunction response.json
```

## Project Structure

```
├── lib/                    # Infrastructure (CDK)
├── application/            # Application logic (Python)
│   ├── src/               # Business logic
│   ├── tests/             # Unit tests
│   └── lambda_handler.py  # Lambda entry point
├── samples/               # Client examples
└── deploy.sh              # Deployment script
```

## License

MIT License
