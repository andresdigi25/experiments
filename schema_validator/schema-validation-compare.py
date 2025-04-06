import time
from datetime import datetime
from typing import List, Dict, Optional, Union
from enum import Enum

# For Cerberus
from cerberus import Validator

# For Pydantic
from pydantic import BaseModel, Field, validator, EmailStr, constr

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
# PYDANTIC IMPLEMENTATION
# -----------------------------------------------------------------------------

def pydantic_validation():
    # Define Pydantic models
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
        street: str
        city: str
        state: constr(min_length=2, max_length=2)
        zip: constr(pattern=r'^\d{5}$')
        country: constr(min_length=2, max_length=2)

    class OrderItem(BaseModel):
        product_id: constr(pattern=r'^P\d{3}$')
        name: str
        price: float = Field(gt=0)
        quantity: int = Field(ge=1)

    class Profile(BaseModel):
        full_name: str
        age: int = Field(ge=18, le=120)
        interests: List[str]
        subscription_tier: SubscriptionTier

    class User(BaseModel):
        id: int
        username: constr(pattern=r'^[a-zA-Z0-9_]{3,20}$')
        email: EmailStr
        signup_date: datetime
        is_active: bool
        profile: Profile

    class Order(BaseModel):
        order_id: constr(pattern=r'^ORD-\d{3}$')
        date: datetime
        items: List[OrderItem]
        total: float = Field(gt=0)
        status: OrderStatus
        shipping_address: Address

        @validator('total')
        def validate_total(cls, v, values):
            if 'items' in values:
                items = values['items']
                calculated_total = sum(item.price * item.quantity for item in items)
                # Allow small floating point differences
                if abs(calculated_total - v) > 0.01:
                    raise ValueError(f"Total {v} doesn't match sum of items {calculated_total}")
            return v

    class Metadata(BaseModel):
        client_version: constr(pattern=r'^\d+\.\d+\.\d+$')
        platform: Platform
        session_duration: int = Field(ge=0)

    class CompleteData(BaseModel):
        user: User
        orders: List[Order]
        metadata: Metadata

    # Validate with Pydantic
    try:
        # Convert string dates to datetime objects for Pydantic
        processed_data = dict(sample_data)
        processed_data['user'] = dict(sample_data['user'])
        processed_data['user']['signup_date'] = datetime.fromisoformat(sample_data['user']['signup_date'])
        
        processed_data['orders'] = []
        for order in sample_data['orders']:
            order_copy = dict(order)
            order_copy['date'] = datetime.fromisoformat(order['date'])
            processed_data['orders'].append(order_copy)
        
        validated_data = CompleteData(**processed_data)
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
    
    # Run Pydantic validation
    pydantic_result, pydantic_errors = pydantic_validation()
    print("Pydantic Validation Result:", pydantic_result)
    if not pydantic_result:
        print("Pydantic Errors:", pydantic_errors)
    
    print("\nStarting performance comparison...\n")
    
    # Smaller number for real benchmark to avoid waiting too long
    iterations = 1000
    
    cerberus_time = run_performance_test(cerberus_validation, "Cerberus", iterations)
    pydantic_time = run_performance_test(pydantic_validation, "Pydantic", iterations)
    
    print("Performance Summary:")
    print(f"Cerberus: {cerberus_time:.4f} seconds for {iterations} validations")
    print(f"Pydantic: {pydantic_time:.4f} seconds for {iterations} validations")
    
    if cerberus_time < pydantic_time:
        print(f"Cerberus was {pydantic_time/cerberus_time:.2f}x faster")
    else:
        print(f"Pydantic was {cerberus_time/pydantic_time:.2f}x faster")
