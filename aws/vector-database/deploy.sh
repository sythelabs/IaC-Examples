#!/bin/bash

# Vector Database Deployment Script
# This script automates the deployment of the vector database infrastructure

set -e

echo "🚀 Vector Database Deployment Script"
echo "====================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Please install it with: npm install -g aws-cdk"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "cdk.json" ]; then
    echo "❌ Please run this script from the vector-database directory"
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo "🧹 Cleaning previous build..."
rm -rf dist

echo "🔧 Building the project..."
npm run build

echo "📦 Installing application dependencies..."
cd application && pip install -r requirements.txt -t . && cd ..

echo "🔍 Checking for CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit > /dev/null 2>&1; then
    echo "🚀 Bootstrapping CDK..."
    cdk bootstrap
else
    echo "✅ CDK is already bootstrapped"
fi

echo "📋 Synthesizing CloudFormation template..."
npm run synth

echo "🚀 Deploying vector database infrastructure..."
npm run deploy

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Important Information:"
echo "========================"
echo "Check the output above for the following endpoints:"
echo "- OpenSearch Domain Endpoint"
echo "- Aurora Cluster Endpoint"
echo "- Vector API Endpoint"
echo "- S3 Bucket Name"
echo "- Database Secret ARN"
echo ""
echo "🔧 Next Steps:"
echo "=============="
echo "1. Set up the database tables (see README.md)"
echo "2. Test the API with the sample client"
echo "3. Configure monitoring and alerts"
echo ""
echo "💡 To destroy the infrastructure when done:"
echo "   npm run destroy" 