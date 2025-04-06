
# ----------------------
# 5. Create Inference Script
# ----------------------
inference_script = """
import os
import re
import json
import numpy as np
import pandas as pd
import joblib
from difflib import SequenceMatcher

# Function definitions (same as in notebook)
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def tokenize_address(address):
    if not address:
        return []
    return re.findall(r'\\b\\w+\\b', address.lower())

def generate_features(addr1, addr2, standardizer):
    features = {}
    std_addr1 = standardizer.standardize(addr1) if addr1 else ""
    std_addr2 = standardizer.standardize(addr2) if addr2 else ""
    if not std_addr1 or not std_addr2:
        return {
            'levenshtein_sim': 0.0,
            'seq_matcher_sim': 0.0,
            'house_num_match': 0.0,
            'unit_match': 0.0,
            'zipcode_match': 0.0,
            'token_count_diff': 0.0
        }
    max_len = max(len(std_addr1), len(std_addr2))
    features['levenshtein_sim'] = 1 - (levenshtein_distance(std_addr1, std_addr2) / max_len if max_len > 0 else 0)
    features['seq_matcher_sim'] = SequenceMatcher(None, std_addr1, std_addr2).ratio()
    comp1 = standardizer.parse_components(std_addr1)
    comp2 = standardizer.parse_components(std_addr2)
    features['house_num_match'] = int(comp1['house_number'] == comp2['house_number'] and comp1['house_number'] is not None)
    features['unit_match'] = int(comp1['unit'] == comp2['unit'] and comp1['unit'] is not None)
    features['zipcode_match'] = int(comp1['zipcode'] == comp2['zipcode'] and comp1['zipcode'] is not None)
    tokens1 = tokenize_address(std_addr1)
    tokens2 = tokenize_address(std_addr2)
    max_tokens = max(len(tokens1), len(tokens2))
    features['token_count_diff'] = abs(len(tokens1) - len(tokens2)) / max_tokens if max_tokens > 0 else 0
    return features

# Model loading and inference
def model_fn(model_dir):
    print(f"Loading model from {model_dir}")
    standardizer = joblib.load(os.path.join(model_dir, 'standardizer.pkl'))
    model = joblib.load(os.path.join(model_dir, 'xgboost_model.pkl'))
    
    with open(os.path.join(model_dir, 'feature_columns.json'), 'r') as f:
        feature_columns = json.load(f)
    
    return {
        'standardizer': standardizer,
        'model': model,
        'feature_columns': feature_columns
    }

def input_fn(request_body, request_content_type):
    if request_content_type == 'application/json':
        return json.loads(request_body)
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, artifacts):
    standardizer = artifacts['standardizer']
    model = artifacts['model']
    feature_columns = artifacts['feature_columns']
    
    # Process input format
    if 'addresses' in input_data:
        pairs = input_data['addresses']
    elif 'addr1' in input_data and 'addr2' in input_data:
        pairs = [input_data]
    else:
        pairs = input_data
    
    results = []
    
    for pair in pairs:
        addr1 = pair.get('addr1', '')
        addr2 = pair.get('addr2', '')
        
        # Generate features
        features = generate_features(addr1, addr2, standardizer)
        
        # Convert to DataFrame
        features_df = pd.DataFrame([features])
        
        # Make sure all expected columns are present
        for col in feature_columns:
            if col not in features_df.columns:
                features_df[col] = 0.0
        
        # Ensure columns are in the correct order
        features_df = features_df[feature_columns]
        
        # Make prediction
        probability = float(model.predict_proba(features_df)[0][1])
        prediction = int(probability >= 0.5)
        
        # Include standardized addresses
        std_addr1 = standardizer.standardize(addr1) if addr1 else ""
        std_addr2 = standardizer.standardize(addr2) if addr2 else ""
        
        results.append({
            'addr1': addr1,
            'addr2': addr2,
            'standardized_addr1': std_addr1,
            'standardized_addr2': std_addr2,
            'match_probability': probability,
            'is_match': prediction
        })
    
    return results

def output_fn(prediction, content_type):
    if content_type == 'application/json':
        return json.dumps(prediction)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
"""

# Write inference script to file
with open(os.path.join(code_dir, 'inference.py'), 'w') as f:
    f.write(inference_script)

# Write requirements file
with open(os.path.join(code_dir, 'requirements.txt'), 'w') as f:
    f.write('pandas>=1.0.0\nnumpy>=1.0.0\nscikit-learn>=0.0.0\nxgboost>=1.0.0\njoblib>=0.0.0\n')

print(f"Inference script saved to {code_dir}/inference.py")

# ----------------------
# 6. Package Model for SageMaker
# ----------------------
# Create a tarball 
import tarfile

with tarfile.open('model.tar.gz', 'w:gz') as tar:
    # Add model directory
    for file in os.listdir(model_dir):
        tar.add(os.path.join(model_dir, file), arcname=os.path.join('model', file))
    # Add code directory
    for file in os.listdir(code_dir):
        tar.add(os.path.join(code_dir, file), arcname=os.path.join('code', file))

print("Model packaged as model.tar.gz")

# ----------------------
# 7. Upload to S3 and Deploy
# ----------------------
try:
    # Get SageMaker execution role
    role = get_execution_role()
except Exception as e:
    print(f"Error getting role: {e}")
    print("Using a placeholder role - please replace with your actual role ARN")
    role = "arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole"

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

# Create SageMaker model
model_name = f'address-matching-model-{int(time.time())}'

model = Model(
    model_data=model_data,
    role=role,
    entry_point='inference.py',
    source_dir='code',
    framework_version='0.23-1',
    py_version='py3',
    name=model_name
)

print(f"SageMaker model created: {model_name}")

# Deploy to endpoint
endpoint_name = f'address-matching-endpoint-{int(time.time())}'

print(f"Deploying model to endpoint: {endpoint_name}")
print("This may take several minutes...")

try:
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type='ml.t2.medium',
        endpoint_name=endpoint_name
    )
    print(f"Model deployed to endpoint: {endpoint_name}")
except Exception as e:
    print(f"Error deploying model: {e}")
    print(f"If the deployment fails, please check the SageMaker console for details.")
    print(f"Endpoint name to use: {endpoint_name}")

print("\nSageMaker deployment complete!")
print("Now you can set up the Lambda function and API Gateway...")
print(f"Remember to use this endpoint name: {endpoint_name}")