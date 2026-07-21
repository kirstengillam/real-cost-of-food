import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class RealCostOfFoodStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── Static site bucket ────────────────────────────────────────────────────
    // Not public — CloudFront accesses it via OAC. Never set publicReadAccess=true.
    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      bucketName: `real-cost-of-food-site-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: false,
    });

    // ── Data bucket ───────────────────────────────────────────────────────────
    // Lambda writes foods_export.json here; GitHub Actions reads it for the
    // site build. Separate from site so the ETL can't accidentally overwrite HTML.
    const dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `real-cost-of-food-data-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: true, // cheap insurance — keeps the last N exports if something goes wrong
    });

    // ── CloudFront Function: rewrite clean URLs to /path/index.html ──────────
    // S3 only serves defaultRootObject at the root. For /foods/eggs, CloudFront
    // must request /foods/eggs/index.html explicitly — this function does that.
    const urlRewriteFn = new cloudfront.Function(this, 'UrlRewriteFunction', {
      code: cloudfront.FunctionCode.fromInline(`
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri.endsWith('/')) {
    request.uri += 'index.html';
  } else if (!uri.includes('.')) {
    request.uri += '/index.html';
  }
  return request;
}
      `),
      runtime: cloudfront.FunctionRuntime.JS_2_0,
      comment: 'Rewrite clean URLs to /index.html for S3 static hosting',
    });

    // ── CloudFront distribution ───────────────────────────────────────────────
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        functionAssociations: [{
          function: urlRewriteFn,
          eventType: cloudfront.FunctionEventType.VIEWER_REQUEST,
        }],
      },
      defaultRootObject: 'index.html',
      // Serve index.html for clean URLs like /foods/eggs (Astro generates eggs/index.html)
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 404,
          responsePagePath: '/404.html',
          ttl: cdk.Duration.seconds(0),
        },
      ],
      // Paste your ACM cert ARN below (must be in us-east-1):
      // Create via ACM console → Request public cert → DNS validation → copy ARN once Issued
      certificate: acm.Certificate.fromCertificateArn(this, 'Cert',
        'arn:aws:acm:us-east-1:111111111111:certificate/4151ad7c-7d42-4724-8579-7a3e0df8b3dd'
      ),
      domainNames: ['realcostoffood.com', 'www.realcostoffood.com'],
    });

    // ── API key parameters (SSM, not Secrets Manager — these are low-sensitivity) ──
    // Create these manually once with:
    //   aws ssm put-parameter --name /rcof/bls-api-key --type SecureString --value YOUR_KEY
    //   aws ssm put-parameter --name /rcof/fdc-api-key --type SecureString --value YOUR_KEY
    const blsKeyParam = ssm.StringParameter.fromSecureStringParameterAttributes(
      this, 'BlsApiKey', { parameterName: '/rcof/bls-api-key' }
    );
    const fdcKeyParam = ssm.StringParameter.fromSecureStringParameterAttributes(
      this, 'FdcApiKey', { parameterName: '/rcof/fdc-api-key' }
    );

    // ── ETL Lambda ────────────────────────────────────────────────────────────
    // Packages the entire etl/ directory. Dependencies are installed in a
    // Lambda layer — see lambda-layer/Makefile.
    const etlFunction = new lambda.Function(this, 'EtlFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../etl'), {
        bundling: {
          // Local bundling: pip-installs into a temp dir alongside the ETL source,
          // then CDK zips it. No Docker required. Works because 'requests' is pure
          // Python — if a compiled C extension is ever added, switch back to Docker.
          local: {
            tryBundle(outputDir: string) {
              const { execSync } = require('child_process');
              const etlDir = path.join(__dirname, '../../etl');
              execSync(`pip3 install -r ${etlDir}/requirements.txt -t ${outputDir} --quiet`);
              execSync(`cp -r ${etlDir}/. ${outputDir}`);
              return true;
            },
          },
          image: lambda.Runtime.PYTHON_3_12.bundlingImage, // fallback (unused)
        },
      }),
      environment: {
        DATA_BUCKET: dataBucket.bucketName,
        BLS_API_KEY_PARAM: blsKeyParam.parameterName,
        FDC_API_KEY_PARAM: fdcKeyParam.parameterName,
        // Tells run_etl.py to write to S3 instead of local disk when set
        EXPORT_TARGET: 's3',
      },
      timeout: cdk.Duration.minutes(5),
      memorySize: 256,
      description: 'Monthly ETL: fetches BLS + USDA data, writes foods_export.json to S3',
    });

    // Grant Lambda permission to read the SSM parameters
    blsKeyParam.grantRead(etlFunction);
    fdcKeyParam.grantRead(etlFunction);

    // Grant Lambda permission to write to the data bucket
    dataBucket.grantPut(etlFunction);

    // ── EventBridge monthly schedule ──────────────────────────────────────────
    // Runs on the 2nd of every month at 06:00 UTC — BLS typically releases the
    // prior month's data on the first Tuesday, so the 2nd is a safe lag.
    new events.Rule(this, 'MonthlyEtlRule', {
      schedule: events.Schedule.cron({ minute: '0', hour: '6', day: '2', month: '*' }),
      targets: [new targets.LambdaFunction(etlFunction)],
      description: 'Trigger ETL on the 2nd of each month',
    });

    // ── GitHub Actions deploy role ────────────────────────────────────────────
    // GitHub Actions assumes this role (via OIDC) to sync site/dist/ to S3
    // and invalidate CloudFront. No long-lived AWS credentials stored in GitHub.
    const githubOidcProvider = new iam.OpenIdConnectProvider(this, 'GithubOidc', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com'],
    });

    const deployRole = new iam.Role(this, 'GithubDeployRole', {
      assumedBy: new iam.WebIdentityPrincipal(githubOidcProvider.openIdConnectProviderArn, {
        StringEquals: {
          // Replace with your actual GitHub org/repo before deploying
          'token.actions.githubusercontent.com:sub': 'repo:kirstengillam/real-cost-of-food:ref:refs/heads/main',
          'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
        },
      }),
      description: 'Assumed by GitHub Actions to deploy site to S3/CloudFront',
    });

    siteBucket.grantReadWrite(deployRole);
    dataBucket.grantReadWrite(deployRole); // read for site build, write for ETL workflow upload
    distribution.grantCreateInvalidation(deployRole);
    blsKeyParam.grantRead(deployRole); // ETL workflow reads keys via aws ssm get-parameter
    fdcKeyParam.grantRead(deployRole);

    // ── RAG Q&A Lambda ───────────────────────────────────────────────────────
    // API keys for the RAG function. Create these once with:
    //   aws ssm put-parameter --name /rcof/voyage-api-key  --type SecureString --value YOUR_KEY
    //   aws ssm put-parameter --name /rcof/anthropic-api-key --type SecureString --value YOUR_KEY
    const voyageKeyParam = ssm.StringParameter.fromSecureStringParameterAttributes(
      this, 'VoyageApiKey', { parameterName: '/rcof/voyage-api-key' }
    );
    const anthropicKeyParam = ssm.StringParameter.fromSecureStringParameterAttributes(
      this, 'AnthropicApiKey', { parameterName: '/rcof/anthropic-api-key' }
    );

    // The deploy-site workflow packages this Lambda fresh on every deploy
    // (pip install voyageai anthropic + lambda_handler.py, ~30MB unzipped).
    // embeddings.json is stored in S3 and fetched at cold start — no Chroma needed.
    const ragFunction = new lambda.Function(this, 'RagFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../rag'), {
        exclude: ['venv/**', 'venv', '*.pyc', '__pycache__', 'chroma_db', 'chunks.json', 'embeddings.json'],
        bundling: {
          local: {
            tryBundle(outputDir: string) {
              const { execSync } = require('child_process');
              const ragDir = path.join(__dirname, '../../rag');
              execSync(`pip3 install voyageai anthropic -t ${outputDir} --quiet --break-system-packages`);
              execSync(`cp ${ragDir}/lambda_handler.py ${outputDir}/`);
              return true;
            },
          },
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
        },
      }),
      environment: {
        // API keys and DATA_BUCKET are injected by the deploy workflow via
        // aws lambda update-function-configuration on every deploy.
        // Set placeholders here so CDK doesn't error on first deploy.
        VOYAGE_API_KEY: 'placeholder',
        ANTHROPIC_API_KEY: 'placeholder',
        DATA_BUCKET: dataBucket.bucketName,
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      description: 'RAG Q&A: embeds question via Voyage, retrieves from S3 embeddings, answers via Claude',
    });

    // SSM grants are kept so the Lambda execution role can read keys if ever
    // needed, but the workflow now injects them as env vars directly.
    voyageKeyParam.grantRead(ragFunction);
    anthropicKeyParam.grantRead(ragFunction);

    // Lambda reads embeddings.json from the data bucket at cold start
    dataBucket.grantRead(ragFunction);

    // Function URL — NONE auth means no IAM invoke permission needed; the
    // deploy role does NOT need grantInvokeUrl (that would create a circular dep).
    const ragFunctionUrl = ragFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ['*'],
        allowedMethods: [lambda.HttpMethod.POST],
        allowedHeaders: ['Content-Type'],
      },
    });

    // Allow the deploy role to update RAG function code (called by deploy-site.yml).
    // Only add to the deploy role's policy — no resource-based policy on the function.
    deployRole.addToPrincipalPolicy(new iam.PolicyStatement({
      actions: ['lambda:UpdateFunctionCode', 'lambda:GetFunction', 'lambda:UpdateFunctionConfiguration'],
      resources: [ragFunction.functionArn],
    }));

    // ── Outputs ───────────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'CloudFrontUrl', {
      value: `https://${distribution.distributionDomainName}`,
      description: 'CloudFront distribution URL',
    });
    new cdk.CfnOutput(this, 'SiteBucketName', {
      value: siteBucket.bucketName,
    });
    new cdk.CfnOutput(this, 'DataBucketName', {
      value: dataBucket.bucketName,
    });
    new cdk.CfnOutput(this, 'DistributionId', {
      value: distribution.distributionId,
      description: 'Used by GitHub Actions to create cache invalidations after deploy',
    });
    new cdk.CfnOutput(this, 'DeployRoleArn', {
      value: deployRole.roleArn,
      description: 'ARN to put in GitHub Actions secret AWS_DEPLOY_ROLE_ARN',
    });
    new cdk.CfnOutput(this, 'RagFunctionName', {
      value: ragFunction.functionName,
      description: 'Put in GitHub Actions secret RAG_FUNCTION_NAME',
    });
    new cdk.CfnOutput(this, 'RagFunctionUrl', {
      value: ragFunctionUrl.url,
      description: 'Put in GitHub Actions secret RAG_FUNCTION_URL (passed to Astro build as PUBLIC_RAG_URL)',
    });
  }
}
