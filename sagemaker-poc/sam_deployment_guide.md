# SAM Deployment Guide for Address Matching API

This guide shows how to deploy the Address Matching API using AWS Serverless Application Model (SAM).

## Prerequisites

1. Install AWS SAM CLI: [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
2. AWS CLI configured with appropriate credentials
3. A deployed SageMaker endpoint (see `sagemaker_deployment_guide.md`)

## Project Structure

Create the following directory structure:

```
address-matching-api/
├── template.yaml         # SAM template
├── lambda/               # Lambda function code
│   ├── lambda_function.py # Lambda handler
│   └── requirements.txt   # Lambda dependencies
└── README.md             # Project documentation
```

## Step 1: Set Up the Project Directory

```bash
# Create directory structure
mkdir -p address-matching-api/lambda

# Copy the template.yaml file
cp template.yaml address-matching-api/

# Navigate to the project directory
cd address-matching-api
```

## Step 2: Create Lambda Function Files

Create a file `lambda/lambda_function.py` with the Lambda code:

```python
# Copy the content from the lambda_function.py artifact
```

Create a file `lambda/requirements.txt`:

```
boto3>=1.24.0
```

## Step 3: Deploy Using SAM CLI

### 3.1: Build the SAM Application

```bash
sam build
```

This command builds the dependencies and prepares the deployment package.

### 3.2: Deploy the Application

#### Option 1: Guided Deployment

```bash
sam deploy --guided
```

Follow the prompts and provide:
- Stack name (e.g., `address-matching-stack`)
- AWS Region
- Parameter values:
  - SageMakerEndpointName: Your deployed SageMaker endpoint name
  - Other parameters can use defaults or be customized

#### Option 2: Deploy with Parameters File

Create a file named `samconfig.toml`:

```toml
version = 0.1
[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "address-matching-stack"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-XXXXXXXXXXXX"
s3_prefix = "address-matching-stack"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
parameter_overrides = "SageMakerEndpointName=your-sagemaker-endpoint-name LambdaFunctionName=address-matching-lambda ApiStageName=prod"
```

Then deploy:

```bash
sam deploy
```

## Step 4: Verify the Deployment

After deployment, SAM will output:
- The API Gateway endpoint URL
- The Lambda function ARN
- A link to the API Gateway console

Test the API using a tool like curl:

```bash
curl -X POST \
  https://your-api-id.execute-api.your-region.amazonaws.com/prod/match-addresses \
  -H 'Content-Type: application/json' \
  -d '{
    "addr1": "123 Main Street, Apt 4B, New York, NY 10001",
    "addr2": "123 Main St, #4B, New York, NY 10001"
  }'
```

Or open the `test_client.html` file in a browser and use the generated API URL.

## Step 5: Make Updates to the Deployment

If you need to update your SAM application:

1. Make changes to your code or template
2. Rebuild: `sam build`
3. Redeploy: `sam deploy`

## Step 6: Cleanup Resources

To remove all deployed resources:

```bash
sam delete
```

## Troubleshooting

### API Gateway CORS Issues

If you encounter CORS errors when testing from a browser:
1. Verify the Cors configuration in the template.yaml
2. Make sure your Lambda returns proper CORS headers

### Lambda Unable to Access SageMaker Endpoint

If your Lambda can't invoke the SageMaker endpoint:
1. Check the IAM policy in template.yaml
2. Verify the SageMakerEndpointName parameter is correct
3. Make sure your Lambda function has the correct environment variable

### Deployment Fails

If SAM deployment fails:
1. Check CloudFormation events in the AWS Console
2. Look for error messages in the SAM CLI output
3. Verify AWS credentials and permissions

## Example SAM CLI Commands

```bash
# Validate template
sam validate

# Test locally (if you have Docker installed)
sam local invoke AddressMatchingFunction -e event.json

# Generate sample event
sam local generate-event apigateway aws-proxy > event.json

# View logs
sam logs -n AddressMatchingFunction --stack-name address-matching-stack

# List all SAM resources
sam list resources --stack-name address-matching-stack

# Get API URL
sam list endpoints --stack-name address-matching-stack
```