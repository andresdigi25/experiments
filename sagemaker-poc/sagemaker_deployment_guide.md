# Detailed SageMaker Model Deployment Guide

This guide provides comprehensive instructions for packaging and deploying a machine learning model to Amazon SageMaker.

## 1. Understanding the SageMaker Model Packaging Structure

SageMaker models require a specific directory structure for deployment:

```
model.tar.gz
├── model/              # Model artifacts directory
│   ├── xgboost_model.pkl    # Your trained model
│   ├── standardizer.pkl     # Address standardizer class
│   └── feature_columns.json # Feature column names
└── code/               # Inference code directory
    ├── inference.py    # Entry point for model inference
    └── requirements.txt # Dependencies for the inference code
```

## 2. Packaging the Model - Step by Step

### 2.1 Create Directory Structure

```bash
mkdir -p model/model
mkdir -p model/code
```

### 2.2 Save Model Artifacts

In your SageMaker notebook, run:

```python
import joblib
import json
import os

# Create model directory
os.makedirs('model/model', exist_ok=True)
os.makedirs('model/code', exist_ok=True)

# Save model artifacts
joblib.dump(model, 'model/model/xgboost_model.pkl')
joblib.dump(standardizer, 'model/model/standardizer.pkl')

# Save feature columns
with open('model/model/feature_columns.json', 'w') as f:
    json.dump(list(X.columns), f)
```

### 2.3 Create Inference Script

Create a file `model/code/inference.py` with the code for model loading and inference (see the provided `inference.py` code).

### 2.4 Create Requirements File

Create a file `model/code/requirements.txt` with:

```
pandas>=1.0.0
numpy>=1.0.0
scikit-learn>=0.0.0
xgboost>=1.0.0
joblib>=0.0.0
```

### 2.5 Create Tarball Package

```python
import tarfile

with tarfile.open('model.tar.gz', 'w:gz') as tar:
    tar.add('model/', arcname='.')
```

## 3. Uploading the Model to S3

```python
import sagemaker
from sagemaker import get_execution_role

# Initialize SageMaker session
sagemaker_session = sagemaker.Session()
bucket = sagemaker_session.default_bucket()
prefix = 'address-matching'

# Upload model to S3
model_data = sagemaker_session.upload_data(
    path='model.tar.gz',
    bucket=bucket,
    key_prefix=prefix
)

print(f"Model uploaded to: {model_data}")
```

## 4. Creating a SageMaker Model

```python
from sagemaker.model import Model
import time

# Get the execution role
role = get_execution_role()

# Define model name
model_name = f'address-matching-model-{int(time.time())}'

# Create the SageMaker model
model = Model(
    model_data=model_data,  # S3 path from the previous step
    role=role,
    entry_point='inference.py',
    source_dir=None,  # Not needed since it's in the tarball
    framework_version='0.23-1',  # Use an appropriate version
    py_version='py3',
    name=model_name
)

print(f"SageMaker model created: {model_name}")
```

## 5. Deploying the Model to an Endpoint

```python
# Define endpoint name
endpoint_name = f'address-matching-endpoint-{int(time.time())}'

# Deploy model to endpoint
predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium',  # Choose appropriate instance type
    endpoint_name=endpoint_name
)

print(f"Model deployed to endpoint: {endpoint_name}")
```

## 6. Testing the Endpoint

```python
import boto3
import json

# Initialize SageMaker runtime client
sagemaker_runtime = boto3.client('sagemaker-runtime')

# Test data
test_data = {
    'addr1': '123 Main Street, Apt 4B, New York, NY 10001',
    'addr2': '123 Main St, #4B, New York, NY 10001'
}

# Invoke endpoint
response = sagemaker_runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    ContentType='application/json',
    Body=json.dumps(test_data)
)

# Parse response
result = json.loads(response['Body'].read().decode())
print(json.dumps(result, indent=2))
```

## 7. Monitoring and Managing the Endpoint

### 7.1 View Endpoint Status in Console

1. Go to the SageMaker console
2. Click on "Endpoints" in the left navigation
3. Find your endpoint and check its status

### 7.2 Monitor with CloudWatch

SageMaker automatically logs metrics to CloudWatch:

1. Go to CloudWatch console
2. Click on "Metrics"
3. Look for "AWS/SageMaker" namespace
4. View metrics like Invocations, InvocationsPerInstance, ModelLatency

### 7.3 View Logs

1. Go to CloudWatch console
2. Click on "Log groups"
3. Find log group: `/aws/sagemaker/Endpoints/{endpoint_name}`

## 8. Updating the Model

To update your model with a new version:

```python
# Create new model version
new_model = Model(
    model_data=new_model_data,  # New model data
    role=role,
    entry_point='inference.py',
    source_dir=None,
    framework_version='0.23-1',
    py_version='py3',
    name=f'{model_name}-v2'
)

# Update the endpoint
predictor = new_model.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium',
    endpoint_name=endpoint_name,  # Same endpoint name
    update_endpoint=True  # This updates the existing endpoint
)
```

## 9. Cleaning Up Resources

When you're done with the endpoint:

```python
# Delete the endpoint
sagemaker_session.delete_endpoint(endpoint_name)

# Delete the endpoint configuration
sagemaker_session.delete_endpoint_config(endpoint_name)

# Delete the model
sagemaker_session.delete_model(model_name)
```

Or in the AWS Console:

1. Go to SageMaker console
2. Click on "Endpoints"
3. Select your endpoint and click "Delete"
4. Go to "Endpoint configurations" and delete that too
5. Go to "Models" and delete the model

## 10. Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check CloudWatch logs for error messages
   - Ensure the inference.py code is compatible with your model
   - Verify the requirements.txt contains all necessary dependencies

2. **Invocation Errors**
   - Ensure the input format matches what inference.py expects
   - Check for memory limitations if the model is large
   - Verify permissions for the execution role

3. **Timeout Issues**
   - Consider increasing the timeout in the endpoint configuration
   - Use a more powerful instance type if processing is slow