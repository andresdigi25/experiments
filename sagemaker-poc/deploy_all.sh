#!/bin/bash

set -e  # Stop on any error

echo "========================================================"
echo "Address Matching Pipeline Deployment Script"
echo "========================================================"
echo

# Check prerequisites
echo "Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting."; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "AWS SAM CLI is required but not installed. Aborting."; exit 1; }
aws sts get-caller-identity >/dev/null 2>&1 || { echo "AWS CLI not configured with valid credentials. Aborting."; exit 1; }

echo "Prerequisites OK!"
echo

# Create project directories
echo "Creating project directories..."
mkdir -p address-matching/lambda
mkdir -p address-matching/sagemaker
echo "Directories created."
echo

# Prompt for SageMaker endpoint name
read -p "Enter SageMaker endpoint name (or leave empty to create new): " ENDPOINT_NAME

if [ -z "$ENDPOINT_NAME" ]; then
    # Will create new endpoint
    ENDPOINT_NAME="address-matching-endpoint-$(date +%s)"
    echo "Will create new endpoint: $ENDPOINT_NAME"
    
    # Copy SageMaker notebook code
    echo "Creating SageMaker code..."
    cat > address-matching/sagemaker/address_matching.py << 'EOF'
# Paste the contents of the address_matching.py artifact here
EOF
    
    echo "SageMaker code created at address-matching/sagemaker/address_matching.py"
    echo "Please run this code in a SageMaker notebook to create your endpoint."
    echo "After endpoint is created, run this script again and enter the endpoint name."
    echo
    echo "Alternatively, you can skip this step if you already have a model deployment."
    echo
    read -p "Do you want to continue with SAM deployment? (y/n): " CONTINUE
    
    if [[ $CONTINUE != "y" && $CONTINUE != "Y" ]]; then
        echo "Deployment paused. Run this script again after creating the SageMaker endpoint."
        exit 0
    fi
fi

# Create Lambda function
echo "Creating Lambda function code..."
cat > address-matching/lambda/lambda_function.py << 'EOF'
# Paste the contents of the lambda_function.py artifact here
EOF

# Create Lambda requirements
cat > address-matching/lambda/requirements.txt << 'EOF'
boto3>=1.24.0
EOF

echo "Lambda code created."
echo

# Create SAM template
echo "Creating SAM template..."
cat > address-matching/template.yaml << EOF
# Paste the contents of the template.yaml artifact here, but replace the endpoint name placeholder
EOF

# Replace the endpoint name placeholder
sed -i "s/Default: address-matching-endpoint/Default: $ENDPOINT_NAME/g" address-matching/template.yaml

echo "SAM template created."
echo

# Create test client
echo "Creating test client..."
cat > address-matching/test_client.html << 'EOF'
# Paste the contents of the test_client.html artifact here
EOF

echo "Test client created at address-matching/test_client.html"
echo

# Deploy with SAM
echo "Ready to deploy with SAM..."
echo "This will create an API Gateway and Lambda function to call your SageMaker endpoint."
read -p "Proceed with deployment? (y/n): " DEPLOY

if [[ $DEPLOY == "y" || $DEPLOY == "Y" ]]; then
    echo "Starting SAM deployment..."
    cd address-matching
    
    # Build and deploy
    sam build
    sam deploy --guided
    
    echo
    echo "Deployment complete!"
    echo "You can find the API URL in the outputs above."
    echo "Use test_client.html to test your API."
else
    echo "Deployment skipped."
    echo "You can deploy manually later with:"
    echo "  cd address-matching"
    echo "  sam build"
    echo "  sam deploy --guided"
fi

echo
echo "Setup complete! Your project files are in the address-matching directory."