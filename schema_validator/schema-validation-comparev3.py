import time
from datetime import datetime
from typing import List, Dict, Optional, Union, ClassVar, Annotated
from enum import Enum

# For Cerberus
from cerberus import Validator

# For Pydantic (v2)
from pydantic import (
    BaseModel, 
    Field, 
    field_validator, 
    model_validator,
    EmailStr, 
    ConfigDict
)

# -----------------------------------------------------------------------------
# Complex Data Structure to Validate
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
# CERBERUS IMPLEMENTATION
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
# OPTIMIZED PYDANTIC V2 IMPLEMENTATION
# -----------------------------------------------------------------------------

def pydantic_optimized_validation():
    # Define Pydantic models with optimization for V2
    class OrderStatus(str, Enum):
        PENDING = "pending"
        PROCESSING = "processing"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    class SubscriptionTier(str, Enum):
        FREE = "free"
        BASIC = "basic"
        PREMIUM = "premium"

    class Platform(str, Enum):
        WEB = "web"
        MOBILE = "mobile"
        DESKTOP = "desktop"

    class Address(BaseModel):
        # Use frozen=True for immutability performance gains
        model_config = ConfigDict(frozen=True)
        
        street: str
        city: str
        state: Annotated[str, Field(min_length=2, max_length=2)]
        zip: Annotated[str, Field(pattern=r'^\d{5}$')]
        country: Annotated[str, Field(min_length=2, max_length=2)]

    class OrderItem(BaseModel):
        model_config = ConfigDict(frozen=True)
        
        product_id: Annotated[str, Field(pattern=r'^P\d{3}$')]
        name: str
        price: Annotated[float, Field(gt=0)]
        quantity: Annotated[int, Field(ge=1)]

    class Profile(BaseModel):
        model_config = ConfigDict(frozen=True)
        
        full_name: str
        age: Annotated[int, Field(ge=18, le=120)]
        interests: List[str]
        subscription_tier: SubscriptionTier

    class User(BaseModel):
        id: int
        username: Annotated[str, Field(pattern=r'^[a-zA-Z0-9_]{3,20}$')]
        email: EmailStr
        signup_date: datetime
        is_active: bool
        profile: Profile

    class Order(BaseModel):
        # Use performance-focused configs
        model_config = ConfigDict(
            validate_default=False,
            extra="forbid",
        )
        
        order_id: Annotated[str, Field(pattern=r'^ORD-\d{3}$')]
        date: datetime
        items: List[OrderItem]
        total: Annotated[float, Field(gt=0)]
        status: OrderStatus
        shipping_address: Address
        
        # Use model_validator instead of field_validator for multi-field validation
        @model_validator(mode='after')
        def validate_total(self):
            items = self.items
            calculated_total = sum(item.price * item.quantity for item in items)
            # Allow small floating point differences
            if abs(calculated_total - self.total) > 0.01:
                raise ValueError(f"Total {self.total} doesn't match sum of items {calculated_total}")
            return self

    class Metadata(BaseModel):
        model_config = ConfigDict(frozen=True)
        
        client_version: Annotated[str, Field(pattern=r'^\d+\.\d+\.\d+$')]
        platform: Platform
        session_duration: Annotated[int, Field(ge=0)]

    class CompleteData(BaseModel):
        # Configure for better performance
        model_config = ConfigDict(
            validate_default=False,
            extra="forbid",
            strict=True,
        )
        
        user: User
        orders: List[Order]
        metadata: Metadata

    # Validate with optimized Pydantic approach
    try:
        # Only modify what's necessary
        user_data = sample_data["user"].copy()
        user_data["signup_date"] = datetime.fromisoformat(sample_data["user"]["signup_date"])
        
        orders_data = []
        for order in sample_data["orders"]:
            # Only modify the date field
            processed_order = dict(order)
            processed_order["date"] = datetime.fromisoformat(order["date"])
            orders_data.append(processed_order)
        
        # Minimal data reconstruction
        processed_data = {
            "user": user_data,
            "orders": orders_data,
            "metadata": sample_data["metadata"]
        }
        
        # Use model_validate which is faster than parse_obj or constructor
        validated_data = CompleteData.model_validate(processed_data)
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
    print("Testing complex data validation...")
    
    # Run Cerberus validation
    cerberus_result, cerberus_errors = cerberus_validation()
    print("Cerberus Validation Result:", cerberus_result)
    if not cerberus_result:
        print("Cerberus Errors:", cerberus_errors)
    
    # Run Pydantic optimized validation
    pydantic_result, pydantic_errors = pydantic_optimized_validation()
    print("Pydantic Optimized Validation Result:", pydantic_result)
    if not pydantic_result:
        print("Pydantic Errors:", pydantic_errors)
    
    print("\nStarting performance comparison...\n")
    
    # Adjust iterations as needed
    iterations = 1000
    
    cerberus_time = run_performance_test(cerberus_validation, "Cerberus", iterations)
    pydantic_time = run_performance_test(pydantic_optimized_validation, "Pydantic Optimized", iterations)
    
    print("Performance Summary:")
    print(f"Cerberus: {cerberus_time:.4f} seconds for {iterations} validations")
    print(f"Pydantic Optimized: {pydantic_time:.4f} seconds for {iterations} validations")
    
    if cerberus_time < pydantic_time:
        print(f"Cerberus was {pydantic_time/cerberus_time:.2f}x faster")
    else:
        print(f"Pydantic was {cerberus_time/pydantic_time:.2f}x faster")
