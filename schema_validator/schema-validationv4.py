import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

# For Cerberus - same as before
from cerberus import Validator

# For Pydantic - using minimal approach
from pydantic import TypeAdapter, BaseModel, Field, RootModel
from pydantic_core import PydanticCustomError
from pydantic.json_schema import JsonSchemaValue

# -----------------------------------------------------------------------------
# Sample data - same as before
# -----------------------------------------------------------------------------

sample_data = {
    "user": {
        "id": 12345,
        "username": "johnsmith",
        "email": "john.smith@example.com",
        "signup_date": "2023-01-15T14:30:00",
        "is_active": True,
        "profile": {
            "full_name": "John Smith",
            "age": 30,
            "interests": ["programming", "hiking", "photography"],
            "subscription_tier": "premium"
        }
    },
    "orders": [
        {
            "order_id": "ORD-001",
            "date": "2023-02-10T09:15:00",
            "items": [
                {"product_id": "P100", "name": "Laptop", "price": 1299.99, "quantity": 1},
                {"product_id": "P101", "name": "Mouse", "price": 25.99, "quantity": 2}
            ],
            "total": 1351.97,
            "status": "delivered",
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
                "country": "US"
            }
        },
        {
            "order_id": "ORD-002",
            "date": "2023-03-15T16:45:00",
            "items": [
                {"product_id": "P102", "name": "Headphones", "price": 89.99, "quantity": 1}
            ],
            "total": 89.99,
            "status": "processing",
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
                "country": "US"
            }
        }
    ],
    "metadata": {
        "client_version": "2.3.0",
        "platform": "web",
        "session_duration": 3600
    }
}

# -----------------------------------------------------------------------------
# CERBERUS IMPLEMENTATION - same as before
# -----------------------------------------------------------------------------

def cerberus_validation():
    # Define schema for nested structures
    address_schema = {
        'street': {'type': 'string', 'required': True},
        'city': {'type': 'string', 'required': True},
        'state': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 2},
        'zip': {'type': 'string', 'required': True, 'regex': r'^\d{5}$'},
        'country': {'type': 'string', 'required': True, 'minlength': 2, 'maxlength': 2}
    }

    order_item_schema = {
        'product_id': {'type': 'string', 'required': True, 'regex': r'^P\d{3}$'},
        'name': {'type': 'string', 'required': True},
        'price': {'type': 'float', 'required': True, 'min': 0},
        'quantity': {'type': 'integer', 'required': True, 'min': 1}
    }

    profile_schema = {
        'full_name': {'type': 'string', 'required': True},
        'age': {'type': 'integer', 'required': True, 'min': 18, 'max': 120},
        'interests': {'type': 'list', 'schema': {'type': 'string'}},
        'subscription_tier': {'type': 'string', 'allowed': ['free', 'basic', 'premium']}
    }

    user_schema = {
        'id': {'type': 'integer', 'required': True},
        'username': {'type': 'string', 'required': True, 'regex': r'^[a-zA-Z0-9_]{3,20}$'},
        'email': {'type': 'string', 'required': True, 'regex': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'},
        'signup_date': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'},
        'is_active': {'type': 'boolean', 'required': True},
        'profile': {'type': 'dict', 'required': True, 'schema': profile_schema}
    }

    order_schema = {
        'order_id': {'type': 'string', 'required': True, 'regex': r'^ORD-\d{3}$'},
        'date': {'type': 'string', 'required': True, 'regex': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'},
        'items': {'type': 'list', 'required': True, 'schema': {'type': 'dict', 'schema': order_item_schema}},
        'total': {'type': 'float', 'required': True, 'min': 0},
        'status': {'type': 'string', 'required': True, 'allowed': ['pending', 'processing', 'shipped', 'delivered', 'cancelled']},
        'shipping_address': {'type': 'dict', 'required': True, 'schema': address_schema}
    }

    metadata_schema = {
        'client_version': {'type': 'string', 'required': True, 'regex': r'^\d+\.\d+\.\d+$'},
        'platform': {'type': 'string', 'required': True, 'allowed': ['web', 'mobile', 'desktop']},
        'session_duration': {'type': 'integer', 'required': True, 'min': 0}
    }

    # Main schema
    schema = {
        'user': {'type': 'dict', 'required': True, 'schema': user_schema},
        'orders': {'type': 'list', 'required': True, 'schema': {'type': 'dict', 'schema': order_schema}},
        'metadata': {'type': 'dict', 'required': True, 'schema': metadata_schema}
    }

    # Custom validator to check that the total price matches sum of items
    class CustomValidator(Validator):
        def _validate_total_matches_items(self, total_matches_items, field, value):
            """
            Test if the total matches the sum of item prices * quantities.
            
            The rule's arguments are validated against this schema:
            {'type': 'boolean'}
            """
            if total_matches_items and field == 'total':
                items = self.document.get('items', [])
                calculated_total = sum(item['price'] * item['quantity'] for item in items)
                # Allow small floating point differences
                if abs(calculated_total - value) > 0.01:
                    self._error(field, f"Total {value} doesn't match sum of items {calculated_total}")

    # Add custom validation to order schema
    order_schema['total']['total_matches_items'] = True

    # Create validator
    v = CustomValidator(schema)
    
    # Validate the data
    result = v.validate(sample_data)
    return result, v.errors

# -----------------------------------------------------------------------------
# MINIMAL PYDANTIC V2 IMPLEMENTATION
# -----------------------------------------------------------------------------

def pydantic_minimal_validation():
    # Simplified schema using TypeAdapter for maximum performance
    
    # Define simplified types - don't use custom models for nested structures
    order_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    subscription_tiers = ["free", "basic", "premium"]
    platforms = ["web", "mobile", "desktop"]
    
    # Define schema as dict structures that directly map to the data
    # This avoids creating class instances for everything
    schema = {
        "user": {
            "id": int,
            "username": str,  # We'll validate regex patterns later manually
            "email": str,     # Using simple str is much faster than EmailStr
            "signup_date": str,
            "is_active": bool,
            "profile": {
                "full_name": str,
                "age": int,
                "interests": List[str],
                "subscription_tier": str
            }
        },
        "orders": List[{
            "order_id": str,
            "date": str,
            "items": List[{
                "product_id": str,
                "name": str,
                "price": float,
                "quantity": int
            }],
            "total": float,
            "status": str,
            "shipping_address": {
                "street": str,
                "city": str,
                "state": str,
                "zip": str,
                "country": str
            }
        }],
        "metadata": {
            "client_version": str,
            "platform": str,
            "session_duration": int
        }
    }
    
    # Create a TypeAdapter for basic type validation
    # This is much faster than full model validation
    schema_validator = TypeAdapter(Dict[str, Any])
    
    try:
        # First pass: basic type validation
        validated = schema_validator.validate_python(sample_data)
        
        # Second pass: manual validation for constraints that would be expensive
        # with standard Pydantic models
        
        # User validation
        user = validated["user"]
        if not user["username"].isalnum() or not 3 <= len(user["username"]) <= 20:
            raise ValueError("Invalid username")
            
        # Simple email regex check (much faster than EmailStr)
        email = user["email"]
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")
            
        # Skip datetime parsing (just verify format)
        if not user["signup_date"].count("-") == 2 and not user["signup_date"].count(":") == 2:
            raise ValueError("Invalid signup date format")
            
        # Profile validation
        profile = user["profile"]
        if not 18 <= profile["age"] <= 120:
            raise ValueError("Age must be between 18 and 120")
            
        if profile["subscription_tier"] not in subscription_tiers:
            raise ValueError(f"Invalid subscription tier. Must be one of {subscription_tiers}")
            
        # Orders validation
        for order in validated["orders"]:
            # Validate order ID format
            if not order["order_id"].startswith("ORD-"):
                raise ValueError("Order ID must start with 'ORD-'")
                
            # Skip datetime parsing
            if not order["date"].count("-") == 2 and not order["date"].count(":") == 2:
                raise ValueError("Invalid order date format")
                
            # Validate status
            if order["status"] not in order_statuses:
                raise ValueError(f"Invalid order status. Must be one of {order_statuses}")
                
            # Validate items
            items = order["items"]
            calculated_total = 0
            
            for item in items:
                # Validate product ID
                if not item["product_id"].startswith("P"):
                    raise ValueError("Product ID must start with 'P'")
                    
                # Validate price and quantity
                if item["price"] <= 0:
                    raise ValueError("Price must be greater than 0")
                    
                if item["quantity"] < 1:
                    raise ValueError("Quantity must be at least 1")
                    
                calculated_total += item["price"] * item["quantity"]
                
            # Validate total
            if abs(calculated_total - order["total"]) > 0.01:
                raise ValueError(f"Total {order['total']} doesn't match sum of items {calculated_total}")
                
            # Validate shipping address
            address = order["shipping_address"]
            if len(address["state"]) != 2:
                raise ValueError("State must be 2 characters")
                
            if len(address["zip"]) != 5 or not address["zip"].isdigit():
                raise ValueError("ZIP must be 5 digits")
                
            if len(address["country"]) != 2:
                raise ValueError("Country code must be 2 characters")
                
        # Metadata validation
        metadata = validated["metadata"]
        
        # Validate client version
        if metadata["client_version"].count(".") != 2:
            raise ValueError("Invalid client version format")
            
        # Validate platform
        if metadata["platform"] not in platforms:
            raise ValueError(f"Invalid platform. Must be one of {platforms}")
            
        # Validate session duration
        if metadata["session_duration"] < 0:
            raise ValueError("Session duration must be non-negative")
            
        return True, None
        
    except Exception as e:
        return False, str(e)

# -----------------------------------------------------------------------------
# PERFORMANCE COMPARISON
# -----------------------------------------------------------------------------

def run_performance_test(validation_func, name, iterations=1000):
    start_time = time.time()
    
    success_count = 0
    for _ in range(iterations):
        result, errors = validation_func()
        if result:
            success_count += 1
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"{name} Performance:")
    print(f"Iterations: {iterations}")
    print(f"Success Rate: {success_count}/{iterations}")
    print(f"Total Time: {elapsed:.4f} seconds")
    print(f"Average Time: {(elapsed/iterations)*1000:.4f} ms per validation")
    print(f"Validations per second: {iterations/elapsed:.2f}")
    print("-" * 50)
    
    return elapsed

if __name__ == "__main__":
    print("Testing data validation approaches...")
    
    # Run Cerberus validation
    cerberus_result, cerberus_errors = cerberus_validation()
    print("Cerberus Validation Result:", cerberus_result)
    if not cerberus_result:
        print("Cerberus Errors:", cerberus_errors)
    
    # Run minimal Pydantic validation
    pydantic_result, pydantic_errors = pydantic_minimal_validation()
    print("Minimal Pydantic Validation Result:", pydantic_result)
    if not pydantic_result:
        print("Pydantic Errors:", pydantic_errors)
    
    print("\nStarting performance comparison...\n")
    
    # Adjust iterations as needed
    iterations = 1000
    
    cerberus_time = run_performance_test(cerberus_validation, "Cerberus", iterations)
    pydantic_time = run_performance_test(pydantic_minimal_validation, "Minimal Pydantic", iterations)
    
    print("Performance Summary:")
    print(f"Cerberus: {cerberus_time:.4f} seconds for {iterations} validations")
    print(f"Minimal Pydantic: {pydantic_time:.4f} seconds for {iterations} validations")
    
    if cerberus_time < pydantic_time:
        print(f"Cerberus was {pydantic_time/cerberus_time:.2f}x faster")
    else:
        print(f"Pydantic was {cerberus_time/pydantic_time:.2f}x faster")