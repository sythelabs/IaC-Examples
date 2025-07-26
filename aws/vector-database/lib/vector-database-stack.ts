import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as opensearch from "aws-cdk-lib/aws-opensearchservice";
import * as rds from "aws-cdk-lib/aws-rds";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as logs from "aws-cdk-lib/aws-logs";

export interface VectorDatabaseStackProps extends cdk.StackProps {
  /**
   * The VPC CIDR block
   * @default '10.0.0.0/16'
   */
  vpcCidr?: string;

  /**
   * The OpenSearch domain name
   * @default 'vector-search-domain'
   */
  openSearchDomainName?: string;

  /**
   * The Aurora cluster identifier
   * @default 'vector-db-cluster'
   */
  auroraClusterIdentifier?: string;

  /**
   * Instance type for OpenSearch data nodes
   * @default 't3.small.search'
   */
  openSearchInstanceType?: string;

  /**
   * Instance type for Aurora instances
   * @default 'db.t3.micro'
   */
  auroraInstanceType?: string;
}

export class VectorDatabaseStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  public readonly openSearchDomain: opensearch.Domain;
  public readonly auroraCluster: rds.DatabaseCluster;
  public readonly vectorApi: apigateway.RestApi;
  public readonly vectorBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: VectorDatabaseStackProps) {
    super(scope, id, props);

    // Create VPC with public and private subnets
    this.vpc = new ec2.Vpc(this, "VectorDatabaseVPC", {
      ipAddresses: ec2.IpAddresses.cidr(props?.vpcCidr || "10.0.0.0/16"),
      maxAzs: 2,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
      natGateways: 1,
    });

    // Create S3 bucket for vector data storage
    this.vectorBucket = new s3.Bucket(this, "VectorDataBucket", {
      bucketName: `${this.account}-${this.region}-vector-data-${Date.now()}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For demo purposes
      autoDeleteObjects: true, // For demo purposes
    });

    // Create OpenSearch Domain for vector search
    const openSearchAccessPolicy = new iam.PolicyStatement({
      actions: ["es:*"],
      effect: iam.Effect.ALLOW,
      principals: [new iam.AnyPrincipal()],
      resources: ["*"],
    });

    this.openSearchDomain = new opensearch.Domain(this, "VectorSearchDomain", {
      domainName: props?.openSearchDomainName || "vector-search-domain",
      version: opensearch.EngineVersion.OPENSEARCH_2_5,
      capacity: {
        dataNodes: 2,
        dataNodeInstanceType:
          props?.openSearchInstanceType || "t3.small.search",
      },
      ebs: {
        volumeSize: 20,
        volumeType: ec2.EbsDeviceVolumeType.GP3,
      },
      vpc: this.vpc,
      vpcSubnets: [{ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }],
      securityGroups: [
        new ec2.SecurityGroup(this, "OpenSearchSecurityGroup", {
          vpc: this.vpc,
          description: "Security group for OpenSearch domain",
          allowAllOutbound: true,
        }),
      ],
      accessPolicies: [openSearchAccessPolicy],
      enforceHttps: true,
      nodeToNodeEncryption: true,
      encryptionAtRest: {
        enabled: true,
      },
      fineGrainedAccessControl: {
        masterUserArn: "arn:aws:iam::" + this.account + ":root",
      },
      logging: {
        slowSearchLogEnabled: true,
        slowIndexLogEnabled: true,
        appLogEnabled: true,
        auditLogEnabled: true,
      },
    });

    // Create Aurora PostgreSQL cluster for metadata storage
    const dbCredentials = new rds.DatabaseSecret(this, "VectorDBCredentials", {
      username: "vectoradmin",
      secretName: "vector-db-credentials",
    });

    this.auroraCluster = new rds.DatabaseCluster(
      this,
      "VectorDatabaseCluster",
      {
        engine: rds.DatabaseClusterEngine.auroraPostgres({
          version: rds.AuroraPostgresEngineVersion.VER_15_4,
        }),
        instanceProps: {
          instanceType: ec2.InstanceType.of(
            ec2.InstanceClass.T3,
            ec2.InstanceSize.MICRO
          ),
          vpc: this.vpc,
          vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
        },
        instances: 2,
        credentials: rds.Credentials.fromSecret(dbCredentials),
        clusterIdentifier:
          props?.auroraClusterIdentifier || "vector-db-cluster",
        storageEncrypted: true,
        backup: {
          retention: cdk.Duration.days(7),
          preferredWindow: "03:00-04:00",
        },
        deletionProtection: false, // For demo purposes
        removalPolicy: cdk.RemovalPolicy.DESTROY, // For demo purposes
      }
    );

    // Create Lambda Layer for dependencies
    const vectorLambdaLayer = new lambda.LayerVersion(
      this,
      "VectorLambdaLayer",
      {
        code: lambda.Code.fromAsset("application"),
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
        description: "Lambda layer containing vector database application",
        layerVersionName: "vector-database-application",
      }
    );

    // Create Lambda function for vector operations
    const vectorLambda = new lambda.Function(this, "VectorOperationsFunction", {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "lambda_handler.handler",
      code: lambda.Code.fromAsset("application"),
      layers: [vectorLambdaLayer],
      environment: {
        OPENSEARCH_ENDPOINT: this.openSearchDomain.domainEndpoint,
        RDS_ENDPOINT: this.auroraCluster.clusterEndpoint.hostname,
        RDS_SECRET_ARN: dbCredentials.secretArn,
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      vpc: this.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    });

    // Grant permissions to Lambda
    this.openSearchDomain.grantReadWrite(vectorLambda);
    this.auroraCluster.grantDataApiAccess(vectorLambda);
    dbCredentials.grantRead(vectorLambda);
    this.vectorBucket.grantReadWrite(vectorLambda);

    // Create API Gateway
    this.vectorApi = new apigateway.RestApi(this, "VectorAPI", {
      restApiName: "Vector Database API",
      description: "API for vector database operations",
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    // Create API resources and methods
    const vectors = this.vectorApi.root.addResource("vectors");

    // POST /vectors - Store vector
    vectors.addMethod("POST", new apigateway.LambdaIntegration(vectorLambda));

    // GET /vectors - Search vectors
    vectors.addMethod("GET", new apigateway.LambdaIntegration(vectorLambda));

    // Create CloudWatch Log Group for better monitoring
    new logs.LogGroup(this, "VectorAPILogs", {
      logGroupName: "/aws/vector-database/api",
      retention: logs.RetentionDays.ONE_WEEK,
    });

    // Output important information
    new cdk.CfnOutput(this, "OpenSearchDomainEndpoint", {
      value: this.openSearchDomain.domainEndpoint,
      description: "OpenSearch Domain Endpoint",
    });

    new cdk.CfnOutput(this, "AuroraClusterEndpoint", {
      value: this.auroraCluster.clusterEndpoint.hostname,
      description: "Aurora Cluster Endpoint",
    });

    new cdk.CfnOutput(this, "VectorAPIEndpoint", {
      value: this.vectorApi.url,
      description: "Vector Database API Endpoint",
    });

    new cdk.CfnOutput(this, "VectorDataBucketName", {
      value: this.vectorBucket.bucketName,
      description: "S3 Bucket for Vector Data Storage",
    });

    new cdk.CfnOutput(this, "DatabaseSecretArn", {
      value: dbCredentials.secretArn,
      description: "Database Credentials Secret ARN",
    });
  }
}
