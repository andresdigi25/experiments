# Import dependencies
import os
import re
import json
import time
import random
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Import SageMaker SDK
import sagemaker
from sagemaker import get_execution_role
from sagemaker.model import Model

print("Starting Address Matching example...")

# ----------------------
# 1. Simple Address Standardizer
# ----------------------
class AddressStandardizer:
    def __init__(self):
        # Street type abbreviations
        self.street_types = {
            'avenue': 'ave',
            'boulevard': 'blvd',
            'street': 'st',
            'road': 'rd',
            'drive': 'dr',
            'lane': 'ln',
            'place': 'pl'
        }
        
        # Unit type abbreviations
        self.unit_types = {
            'apartment': 'apt',
            'suite': 'ste',
            'unit': 'unit'
        }
        
        # Patterns for components
        self.house_number_pattern = re.compile(r'^\d+')
        self.zip_pattern = re.compile(r'\b\d{5}(?:-\d{4})?\b')
        self.unit_pattern = re.compile(r'\b(?:apt|suite|ste|unit|#)\s*(?:[a-zA-Z0-9-]+)\b', re.IGNORECASE)
    
    def standardize(self, address):
        if not address:
            return ""
            
        # Convert to lowercase
        addr = address.lower()
        
        # Replace periods and commas with spaces
        addr = addr.replace('.', ' ').replace(',', ' ')
        
        # Replace hash/pound sign with 'unit'
        addr = re.sub(r'#\s*', 'unit ', addr)
        
        # Standardize street types
        for full, abbr in self.street_types.items():
            addr = re.sub(r'\b' + full + r'\b', abbr, addr)
            addr = re.sub(r'\b' + abbr + r'\.\b', abbr, addr)
        
        # Standardize unit types
        for full, abbr in self.unit_types.items():
            addr = re.sub(r'\b' + full + r'\b', abbr, addr)
            addr = re.sub(r'\b' + abbr + r'\.\b', abbr, addr)
        
        # Remove extra whitespace
        addr = ' '.join(addr.split())
        
        return addr
    
    def parse_components(self, address):
        components = {
            'house_number': None,
            'unit': None,
            'zipcode': None
        }
        
        # Extract ZIP code
        zip_match = self.zip_pattern.search(address)
        if zip_match:
            components['zipcode'] = zip_match.group()
        
        # Extract unit information
        unit_match = self.unit_pattern.search(address)
        if unit_match:
            components['unit'] = unit_match.group()
        
        # Extract house number
        house_match = self.house_number_pattern.search(address)
        if house_match:
            components['house_number'] = house_match.group()
        
        return components

# ----------------------
# 2. Feature Generation
# ----------------------
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
    return re.findall(r'\b\w+\b', address.lower())

def generate_features(addr1, addr2, standardizer):
    features = {}
    
    # Standardize addresses
    std_addr1 = standardizer.standardize(addr1) if addr1 else ""
    std_addr2 = standardizer.standardize(addr2) if addr2 else ""
    
    # Handle empty addresses
    if not std_addr1 or not std_addr2:
        return {
            'levenshtein_sim': 0.0,
            'seq_matcher_sim': 0.0,
            'house_num_match': 0.0,
            'unit_match': 0.0,
            'zipcode_match': 0.0,
            'token_count_diff': 0.0
        }
    
    # String similarity metrics
    max_len = max(len(std_addr1), len(std_addr2))
    features['levenshtein_sim'] = 1 - (levenshtein_distance(std_addr1, std_addr2) / max_len if max_len > 0 else 0)
    features['seq_matcher_sim'] = SequenceMatcher(None, std_addr1, std_addr2).ratio()
    
    # Extract components
    comp1 = standardizer.parse_components(std_addr1)
    comp2 = standardizer.parse_components(std_addr2)
    
    # Component matching
    features['house_num_match'] = int(comp1['house_number'] == comp2['house_number'] and comp1['house_number'] is not None)
    features['unit_match'] = int(comp1['unit'] == comp2['unit'] and comp1['unit'] is not None)
    features['zipcode_match'] = int(comp1['zipcode'] == comp2['zipcode'] and comp1['zipcode'] is not None)
    
    # Token differences
    tokens1 = tokenize_address(std_addr1)
    tokens2 = tokenize_address(std_addr2)
    max_tokens = max(len(tokens1), len(tokens2))
    features['token_count_diff'] = abs(len(tokens1) - len(tokens2)) / max_tokens if max_tokens > 0 else 0
    
    return features

# ----------------------
# 3. Sample Data Generation
# ----------------------
def generate_sample_data(n_samples=200):
    # Base addresses
    base_addresses = [
        {'id': 'A1', 'address': '123 Main Street, Apt 4B, New York, NY 10001'},
        {'id': 'A2', 'address': '456 Oak Avenue, Suite 202, Los Angeles, CA 90001'},
        {'id': 'A3', 'address': '789 Pine Road, Chicago, IL 60601'},
        {'id': 'A4', 'address': '321 Cedar Boulevard, San Francisco, CA 94101'},
        {'id': 'A5', 'address': '555 Maple Lane, Boston, MA 02101'}
    ]
    
    # Create variations
    def create_variation(address):
        addr = address['address']
        variations = [
            addr.replace('Street', 'St').replace('Avenue', 'Ave').replace('Road', 'Rd'),
            addr.replace('Boulevard', 'Blvd').replace('Lane', 'Ln'),
            addr.replace('Apartment', 'Apt').replace('Suite', 'Ste').replace('Unit', '#'),
            addr.replace(', ', ' ').replace(', ', ' ')
        ]
        return {'id': f"V{address['id'][1:]}", 'address': random.choice(variations)}
    
    # Generate positive pairs
    positive_pairs = []
    for base_addr in base_addresses:
        var_addr = create_variation(base_addr)
        positive_pairs.append({
            'addr1': base_addr['address'],
            'addr2': var_addr['address'],
            'is_match': 1
        })
    
    # Generate negative pairs
    negative_pairs = []
    for i in range(len(base_addresses)):
        for j in range(i + 1, len(base_addresses)):
            negative_pairs.append({
                'addr1': base_addresses[i]['address'],
                'addr2': base_addresses[j]['address'],
                'is_match': 0
            })
    
    # Combine and shuffle
    all_pairs = positive_pairs + negative_pairs
    random.shuffle(all_pairs)
    
    # Duplicate to get more samples
    while len(all_pairs) < n_samples:
        all_pairs.extend(all_pairs[:min(len(all_pairs), n_samples - len(all_pairs))])
    
    return all_pairs[:n_samples]

# ----------------------
# 4. Train and Save Model
# ----------------------
# Create model directories
model_dir = 'model'
code_dir = 'code'
os.makedirs(model_dir, exist_ok=True)
os.makedirs(code_dir, exist_ok=True)

# Create standardizer
standardizer = AddressStandardizer()

# Generate sample data
training_data = generate_sample_data(n_samples=200)
print(f"Generated {len(training_data)} training samples")

# Process data
features_list = []
labels = []

for pair in training_data:
    features = generate_features(pair['addr1'], pair['addr2'], standardizer)
    features_list.append(features)
    labels.append(pair['is_match'])

# Convert to DataFrame
X = pd.DataFrame(features_list)
y = np.array(labels)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
print("Training XGBoost model...")
model = xgb.XGBClassifier(
    n_estimators=50,
    learning_rate=0.1,
    max_depth=3,
    objective='binary:logistic',
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy:.4f}")

# Save model artifacts
joblib.dump(standardizer, os.path.join(model_dir, 'standardizer.pkl'))
joblib.dump(model, os.path.join(model_dir, 'xgboost_model.pkl'))

# Save feature columns
with open(os.path.join(model_dir, 'feature_columns.json'), 'w') as f:
    json.dump(list(X.columns), f)

print(f"Model saved to {model_dir} directory")
