#!/usr/bin/env python3
import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key.startswith('_') or key in ['args', 'exc_info', 'exc_text', 'levelname', 
                                             'levelno', 'lineno', 'module', 'msecs', 'msg', 
                                             'name', 'pathname', 'process', 'processName', 
                                             'relativeCreated', 'stack_info', 'thread', 
                                             'threadName', 'created', 'filename', 'funcName']:
                continue
            log_record[key] = value
            
        return json.dumps(log_record)

# Setup logger
logger = logging.getLogger("ecommerce")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

# Optional file handler
file_handler = logging.FileHandler("ecommerce.log")
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

# Sample data
products = {
    "p1": {"id": "p1", "name": "Laptop", "price": 1299.99, "weight": 2.5, "stock": 10},
    "p2": {"id": "p2", "name": "Smartphone", "price": 799.99, "weight": 0.2, "stock": 25},
    "p3": {"id": "p3", "name": "Headphones", "price": 149.99, "weight": 0.3, "stock": 50},
    "p4": {"id": "p4", "name": "Monitor", "price": 349.99, "weight": 5.0, "stock": 15},
    "p5": {"id": "p5", "name": "Keyboard", "price": 99.99, "weight": 1.0, "stock": 30},
}

payment_methods = ["credit_card", "paypal", "bank_transfer", "crypto"]
shipping_methods = ["standard", "express", "overnight", "pickup"]
user_locations = ["New York", "London", "Tokyo", "Sydney", "Berlin"]

# Tracing utility
class TracingContext:
    def __init__(self, correlation_id: str = None, parent_span: str = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.parent_span = parent_span
        self.start_time = time.time()
        
    def create_child_context(self, span_name: str) -> 'TracingContext':
        """Create a new context for a child operation."""
        return TracingContext(
            correlation_id=self.correlation_id,
            parent_span=span_name
        )

# Timing decorator for method-level tracing
def trace(span_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract context from kwargs or create new one
            ctx = kwargs.get('ctx') or TracingContext()
            
            # Create a new span for this operation
            current_span = span_name
            start_time = time.time()
            
            # Add the context back to kwargs
            kwargs['ctx'] = ctx
            
            # Prepare common log fields
            log_fields = {
                'correlation_id': ctx.correlation_id,
                'span': current_span,
                'parent_span': ctx.parent_span,
                'duration_ms': 0
            }
            
            # Log operation start
            logger.info(f"Started: {current_span}", extra=log_fields)
            
            # Add random small delay to simulate processing time
            simulation_delay = random.uniform(0.01, 0.2)
            time.sleep(simulation_delay)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log success
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Completed: {current_span}",
                    extra={
                        **log_fields,
                        'duration_ms': f"{duration_ms:.2f}",
                        'status': 'success',
                    }
                )
                return result
                
            except Exception as e:
                # Log error
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Failed: {current_span} - {str(e)}",
                    extra={
                        **log_fields,
                        'duration_ms': f"{duration_ms:.2f}",
                        'status': 'error',
                        'error_message': str(e),
                        'error_type': type(e).__name__
                    }
                )
                raise
                
        return wrapper
    return decorator

# Simulated e-commerce flow methods
class EcommerceService:
    
    @trace(span_name="browse_products")
    def browse_products(self, search_term: str = None, filters: Dict = None, ctx: TracingContext = None) -> List[Dict]:
        """Browse and filter products."""
        filters = filters or {}
        
        # Log inputs
        logger.info(
            "Browsing products",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'browse_products',
                'search_term': search_term,
                'filters': filters
            }
        )
        
        # Filter products based on search term and filters
        filtered_products = []
        price_min = filters.get('price_min', 0)
        price_max = filters.get('price_max', float('inf'))
        
        for product in products.values():
            # Skip products that don't match price filter
            if product['price'] < price_min or product['price'] > price_max:
                continue
                
            # Apply search term if provided
            if search_term and search_term.lower() not in product['name'].lower():
                continue
                
            filtered_products.append(product)
        
        # Log results
        logger.info(
            f"Found {len(filtered_products)} products matching criteria",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'browse_products',
                'product_count': len(filtered_products)
            }
        )
        
        # Simulate potential errors
        if random.random() < 0.05:  # 5% chance of error
            error_type = random.choice(["db_timeout", "search_index_error"])
            logger.error(
                f"Search error: {error_type}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'browse_products',
                    'error_type': error_type
                }
            )
            if error_type == "db_timeout":
                raise TimeoutError("Database query timed out")
            else:
                raise ValueError("Search index error")
        
        return filtered_products
    
    @trace(span_name="add_to_cart")
    def add_to_cart(self, cart_id: str, product_id: str, quantity: int, 
                   ctx: TracingContext = None) -> Dict:
        """Add a product to the shopping cart."""
        # Validate product exists
        if product_id not in products:
            logger.error(
                f"Product not found: {product_id}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'add_to_cart',
                    'product_id': product_id,
                    'error': 'product_not_found'
                }
            )
            raise ValueError(f"Product not found: {product_id}")
            
        product = products[product_id]
        
        # Check stock availability
        stock_ctx = ctx.create_child_context("check_stock")
        in_stock = self.check_stock(product_id, quantity, ctx=stock_ctx)
        
        if not in_stock:
            logger.error(
                f"Insufficient stock for product: {product_id}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'add_to_cart',
                    'product_id': product_id,
                    'requested_quantity': quantity,
                    'available_stock': product['stock'],
                    'error': 'insufficient_stock'
                }
            )
            raise ValueError(f"Insufficient stock for product: {product_id}")
        
        # Calculate item total
        item_total = product['price'] * quantity
        
        # Log success
        logger.info(
            f"Added {quantity} of {product['name']} to cart {cart_id}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'add_to_cart',
                'cart_id': cart_id,
                'product_id': product_id,
                'product_name': product['name'],
                'quantity': quantity,
                'unit_price': product['price'],
                'item_total': item_total
            }
        )
        
        return {
            "cart_id": cart_id,
            "product": product,
            "quantity": quantity,
            "item_total": item_total
        }
    
    @trace(span_name="check_stock")
    def check_stock(self, product_id: str, quantity: int, ctx: TracingContext = None) -> bool:
        """Check if a product is in stock."""
        # Simulate database lookup
        if product_id not in products:
            logger.error(
                f"Product not found during stock check: {product_id}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'check_stock',
                    'product_id': product_id,
                    'error': 'product_not_found'
                }
            )
            return False
            
        product = products[product_id]
        available = product['stock'] >= quantity
        
        logger.info(
            f"Stock check for product {product_id}: {'Available' if available else 'Unavailable'}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'check_stock',
                'product_id': product_id,
                'product_name': product['name'],
                'requested_quantity': quantity,
                'available_stock': product['stock'],
                'is_available': available
            }
        )
        
        # Simulate occasional stock check delays
        if random.random() < 0.2:  # 20% chance of delay
            delay = random.uniform(0.5, 1.5)
            logger.info(
                f"Stock database experiencing slowness: {delay:.2f}s delay",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'check_stock',
                    'delay_seconds': f"{delay:.2f}",
                    'delay_reason': 'database_slowness'
                }
            )
            time.sleep(delay)
        
        return available
    
    @trace(span_name="process_payment")
    def process_payment(self, order_id: str, amount: float, payment_method: str, 
                       payment_details: Dict, ctx: TracingContext = None) -> Dict:
        """Process a payment for an order."""
        # Log payment attempt
        logger.info(
            f"Processing payment for order {order_id}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'process_payment',
                'order_id': order_id,
                'amount': amount,
                'payment_method': payment_method,
                'currency': 'USD'
            }
        )
        
        # Create a transaction ID
        transaction_id = f"txn-{uuid.uuid4().hex[:8]}"
        
        # Simulate payment processing steps
        # 1. Validate payment details
        validation_ctx = ctx.create_child_context("validate_payment")
        validation_result = self.validate_payment_details(
            payment_method, payment_details, ctx=validation_ctx
        )
        
        if not validation_result['valid']:
            logger.error(
                f"Payment validation failed: {validation_result['reason']}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'process_payment',
                    'order_id': order_id,
                    'transaction_id': transaction_id,
                    'error': 'validation_failed',
                    'reason': validation_result['reason']
                }
            )
            raise ValueError(f"Payment validation failed: {validation_result['reason']}")
        
        # 2. Connect to payment gateway (simulated)
        logger.info(
            f"Connecting to payment gateway for {payment_method}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'process_payment.gateway_connection',
                'order_id': order_id,
                'transaction_id': transaction_id,
                'payment_method': payment_method
            }
        )
        
        # Simulate gateway processing time
        gateway_time = random.uniform(0.5, 2.0)
        time.sleep(gateway_time)
        
        # 3. Process payment (with simulated failures)
        success_rate = {
            "credit_card": 0.95,
            "paypal": 0.92,
            "bank_transfer": 0.99,
            "crypto": 0.85
        }.get(payment_method, 0.9)
        
        payment_success = random.random() < success_rate
        
        if not payment_success:
            error_reasons = {
                "credit_card": ["insufficient_funds", "card_expired", "security_code_invalid"],
                "paypal": ["account_issue", "connection_error"],
                "bank_transfer": ["account_number_invalid"],
                "crypto": ["network_congestion", "insufficient_confirmation"]
            }
            
            reason = random.choice(error_reasons.get(payment_method, ["processing_error"]))
            
            logger.error(
                f"Payment failed: {reason}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'process_payment',
                    'order_id': order_id,
                    'transaction_id': transaction_id,
                    'payment_method': payment_method,
                    'gateway_time_ms': f"{gateway_time * 1000:.2f}",
                    'error': 'payment_failed',
                    'reason': reason
                }
            )
            
            raise ValueError(f"Payment failed: {reason}")
        
        # Log successful payment
        logger.info(
            f"Payment successful for order {order_id}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'process_payment',
                'order_id': order_id,
                'transaction_id': transaction_id,
                'payment_method': payment_method,
                'amount': amount,
                'currency': 'USD',
                'gateway_time_ms': f"{gateway_time * 1000:.2f}"
            }
        )
        
        return {
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @trace(span_name="validate_payment_details")
    def validate_payment_details(self, payment_method: str, payment_details: Dict, 
                                ctx: TracingContext = None) -> Dict:
        """Validate payment details for a specific payment method."""
        validation_errors = []
        
        # Common validation for all methods
        if 'name' not in payment_details or not payment_details['name']:
            validation_errors.append("name_required")
        
        # Method-specific validation
        if payment_method == "credit_card":
            if 'card_number' not in payment_details:
                validation_errors.append("card_number_required")
            elif not self._is_valid_card_number(payment_details['card_number']):
                validation_errors.append("card_number_invalid")
                
            if 'expiry' not in payment_details:
                validation_errors.append("expiry_required")
            elif not self._is_valid_expiry(payment_details['expiry']):
                validation_errors.append("expiry_invalid")
                
            if 'cvv' not in payment_details:
                validation_errors.append("cvv_required")
            elif not self._is_valid_cvv(payment_details['cvv']):
                validation_errors.append("cvv_invalid")
                
        elif payment_method == "paypal":
            if 'email' not in payment_details:
                validation_errors.append("email_required")
            elif not self._is_valid_email(payment_details['email']):
                validation_errors.append("email_invalid")
                
        elif payment_method == "bank_transfer":
            if 'account_number' not in payment_details:
                validation_errors.append("account_number_required")
            if 'routing_number' not in payment_details:
                validation_errors.append("routing_number_required")
                
        elif payment_method == "crypto":
            if 'wallet_address' not in payment_details:
                validation_errors.append("wallet_address_required")
        
        # Log validation details
        logger.info(
            f"Validating {payment_method} payment details",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'validate_payment_details',
                'payment_method': payment_method,
                'validation_errors': validation_errors,
                'is_valid': len(validation_errors) == 0
            }
        )
        
        if validation_errors:
            return {
                "valid": False,
                "reason": ", ".join(validation_errors)
            }
        else:
            return {
                "valid": True
            }
    
    # Helper methods for validation
    def _is_valid_card_number(self, card_number: str) -> bool:
        # Simple validation for demo purposes
        return card_number and len(card_number) >= 13 and len(card_number) <= 19
    
    def _is_valid_expiry(self, expiry: str) -> bool:
        return expiry and len(expiry) == 5 and expiry[2] == '/'
    
    def _is_valid_cvv(self, cvv: str) -> bool:
        return cvv and len(cvv) >= 3 and len(cvv) <= 4
    
    def _is_valid_email(self, email: str) -> bool:
        return email and '@' in email and '.' in email.split('@')[1]
    
    @trace(span_name="create_shipment")
    def create_shipment(self, order_id: str, shipping_address: Dict, 
                       items: List[Dict], shipping_method: str, 
                       ctx: TracingContext = None) -> Dict:
        """Create a shipment for an order."""
        shipment_id = f"shp-{uuid.uuid4().hex[:8]}"
        
        # Log shipment creation
        logger.info(
            f"Creating shipment for order {order_id}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'create_shipment',
                'order_id': order_id,
                'shipment_id': shipment_id,
                'shipping_method': shipping_method,
                'item_count': len(items)
            }
        )
        
        # Calculate package details
        total_weight = sum(item['product']['weight'] * item['quantity'] for item in items)
        
        # Determine estimated delivery date based on shipping method
        shipping_days = {
            "standard": random.randint(3, 7),
            "express": random.randint(2, 3),
            "overnight": 1,
            "pickup": 0
        }.get(shipping_method, 5)
        
        # Check stock and allocate inventory
        inventory_ctx = ctx.create_child_context("allocate_inventory")
        allocation_success = self.allocate_inventory(items, ctx=inventory_ctx)
        
        if not allocation_success:
            logger.error(
                f"Failed to allocate inventory for shipment",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'create_shipment',
                    'order_id': order_id,
                    'shipment_id': shipment_id,
                    'error': 'inventory_allocation_failed'
                }
            )
            raise ValueError("Failed to allocate inventory for shipment")
        
        # Validate shipping address
        address_ctx = ctx.create_child_context("validate_address")
        address_validation = self.validate_shipping_address(shipping_address, ctx=address_ctx)
        
        if not address_validation['valid']:
            logger.error(
                f"Invalid shipping address: {address_validation['reason']}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'create_shipment',
                    'order_id': order_id,
                    'shipment_id': shipment_id,
                    'error': 'invalid_address',
                    'reason': address_validation['reason']
                }
            )
            raise ValueError(f"Invalid shipping address: {address_validation['reason']}")
        
        # Generate tracking number
        tracking_number = f"TRK{random.randint(10000000, 99999999)}"
        
        # Simulate occasional shipping provider issues
        if random.random() < 0.1:  # 10% chance of issue
            issue_type = random.choice(["connection_timeout", "service_unavailable", "rate_limit"])
            
            logger.error(
                f"Shipping provider API issue: {issue_type}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'create_shipment.provider_api',
                    'order_id': order_id,
                    'shipment_id': shipment_id,
                    'error': 'provider_api_issue',
                    'issue_type': issue_type
                }
            )
            
            if random.random() < 0.5:  # 50% chance the issue is terminal
                raise ConnectionError(f"Shipping provider API issue: {issue_type}")
        
        # Log successful shipment creation
        logger.info(
            f"Shipment created successfully: {shipment_id}",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'create_shipment',
                'order_id': order_id,
                'shipment_id': shipment_id,
                'tracking_number': tracking_number,
                'shipping_method': shipping_method,
                'estimated_days': shipping_days,
                'total_weight_kg': total_weight
            }
        )
        
        return {
            "shipment_id": shipment_id,
            "order_id": order_id,
            "tracking_number": tracking_number,
            "shipping_method": shipping_method,
            "estimated_delivery_days": shipping_days,
            "total_weight_kg": total_weight,
            "status": "created"
        }
    
    @trace(span_name="allocate_inventory")
    def allocate_inventory(self, items: List[Dict], ctx: TracingContext = None) -> bool:
        """Allocate inventory for a list of items."""
        # Log inventory allocation start
        logger.info(
            f"Allocating inventory for {len(items)} items",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'allocate_inventory',
                'item_count': len(items)
            }
        )
        
        # Check each item
        for item in items:
            product_id = item['product']['id']
            quantity = item['quantity']
            
            # Check if product exists in inventory
            if product_id not in products:
                logger.error(
                    f"Product not found in inventory: {product_id}",
                    extra={
                        'correlation_id': ctx.correlation_id,
                        'span': 'allocate_inventory',
                        'product_id': product_id,
                        'error': 'product_not_found'
                    }
                )
                return False
            
            # Check if enough stock is available
            if products[product_id]['stock'] < quantity:
                logger.error(
                    f"Insufficient stock for product: {product_id}",
                    extra={
                        'correlation_id': ctx.correlation_id,
                        'span': 'allocate_inventory',
                        'product_id': product_id,
                        'requested_quantity': quantity,
                        'available_stock': products[product_id]['stock'],
                        'error': 'insufficient_stock'
                    }
                )
                return False
            
            # Allocate inventory (simulate)
            previous_stock = products[product_id]['stock']
            products[product_id]['stock'] -= quantity
            
            logger.info(
                f"Allocated {quantity} units of product {product_id}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'allocate_inventory',
                    'product_id': product_id,
                    'product_name': products[product_id]['name'],
                    'allocated_quantity': quantity,
                    'previous_stock': previous_stock,
                    'new_stock': products[product_id]['stock']
                }
            )
        
        # Simulate occasional inventory system lag
        if random.random() < 0.15:  # 15% chance of delay
            delay = random.uniform(0.3, 1.0)
            logger.info(
                f"Inventory system experiencing lag: {delay:.2f}s delay",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'allocate_inventory',
                    'delay_seconds': f"{delay:.2f}",
                    'delay_reason': 'system_lag'
                }
            )
            time.sleep(delay)
        
        return True
    
    @trace(span_name="validate_shipping_address")
    def validate_shipping_address(self, address: Dict, ctx: TracingContext = None) -> Dict:
        """Validate a shipping address."""
        required_fields = ['name', 'street', 'city', 'postal_code', 'country']
        missing_fields = [field for field in required_fields if field not in address or not address[field]]
        
        # Log address validation
        logger.info(
            f"Validating shipping address",
            extra={
                'correlation_id': ctx.correlation_id,
                'span': 'validate_shipping_address',
                'address_country': address.get('country', 'unknown'),
                'address_city': address.get('city', 'unknown'),
                'missing_fields': missing_fields,
                'is_valid': len(missing_fields) == 0
            }
        )
        
        if missing_fields:
            return {
                "valid": False,
                "reason": f"Missing required fields: {', '.join(missing_fields)}"
            }
            
        # Simulate address validation service (with occasional slowness)
        if random.random() < 0.2:  # 20% chance of slow validation
            delay = random.uniform(0.5, 1.5)
            logger.info(
                f"Address validation service slow: {delay:.2f}s delay",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'validate_shipping_address.service',
                    'delay_seconds': f"{delay:.2f}",
                    'delay_reason': 'service_slowness'
                }
            )
            time.sleep(delay)
        
        # Simulate some addresses being invalid
        if random.random() < 0.05:  # 5% chance of invalid address
            invalid_reason = random.choice([
                "address_not_found", 
                "invalid_postal_code", 
                "undeliverable_address"
            ])
            
            logger.error(
                f"Address validation failed: {invalid_reason}",
                extra={
                    'correlation_id': ctx.correlation_id,
                    'span': 'validate_shipping_address',
                    'error': 'address_validation_failed',
                    'reason': invalid_reason,
                    'address_country': address.get('country', 'unknown'),
                    'address_city': address.get('city', 'unknown')
                }
            )
            
            return {
                "valid": False,
                "reason": invalid_reason
            }
        
        return {
            "valid": True
        }

# Simulate a full order process
def simulate_order_process():
    # Create a correlation ID for the entire process
    correlation_id = str(uuid.uuid4())
    main_ctx = TracingContext(correlation_id=correlation_id)
    
    # Log start of order process
    logger.info(
        "Starting order process simulation",
        extra={
            'correlation_id': correlation_id,
            'span': 'order_process',
            'simulation_id': f"sim-{uuid.uuid4().hex[:6]}"
        }
    )
    
    # Initialize service
    service = EcommerceService()
    
    try:
        # 1. Browse products
        filters = {
            'price_min': 100,
            'price_max': 1000
        }
        
        browse_ctx = main_ctx.create_child_context("browse_products")
        found_products = service.browse_products(
            search_term="phone", 
            filters=filters, 
            ctx=browse_ctx
        )
        
        if not found_products:
            logger.error(
                "No products found matching criteria",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'order_process',
                    'error': 'no_products_found'
                }
            )
            return
        
        # 2. Add products to cart
        cart_id = f"cart-{uuid.uuid4().hex[:8]}"
        cart_items = []
        
        for product in found_products[:2]:  # Add up to 2 products
            quantity = random.randint(1, 3)
            
            add_ctx = main_ctx.create_child_context("add_to_cart")
            try:
                cart_item = service.add_to_cart(
                    cart_id=cart_id,
                    product_id=product['id'],
                    quantity=quantity,
                    ctx=add_ctx
                )
                cart_items.append(cart_item)
            except ValueError as e:
                logger.error(
                    f"Failed to add product to cart: {str(e)}",
                    extra={
                        'correlation_id': correlation_id,
                        'span': 'order_process',
                        'cart_id': cart_id,
                        'product_id': product['id'],
                        'error': 'add_to_cart_failed',
                        'error_detail': str(e)
                    }
                )
                continue
        
        if not cart_items:
            logger.error(
                "Failed to add any products to cart",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'order_process',
                    'cart_id': cart_id,
                    'error': 'empty_cart'
                }
            )
            return
        
        # 3. Create order from cart
        order_id = f"order-{uuid.uuid4().hex[:8]}"
        
        # Calculate order totals
        subtotal = sum(item['item_total'] for item in cart_items)
        tax = subtotal * 0.08  # 8% tax
        shipping_cost = 15.0 if subtotal < 150 else 0.0  # Free shipping over $150
        total = subtotal + tax + shipping_cost
        
        logger.info(
            f"Created order {order_id} from cart {cart_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'create_order',
                'order_id': order_id,
                'cart_id': cart_id,
                'item_count': len(cart_items),
                'subtotal': subtotal,
                'tax': tax,
                'shipping_cost': shipping_cost,
                'total': total
            }
        )
        
        # 4. Process payment
        payment_method = random.choice(payment_methods)
        
        # Generate payment details based on method
        payment_details = {"name": "John Doe"}
        
        if payment_method == "credit_card":
            payment_details.update({
                "card_number": "4111111111111111",
                "expiry": "12/25",
                "cvv": "123"
            })
        elif payment_method == "paypal":
            payment_details.update({
                "email": "john.doe@example.com"
            })
        elif payment_method == "bank_transfer":
            payment_details.update({
                "account_number": "12345678",
                "routing_number": "87654321"
            })
        elif payment_method == "crypto":
            payment_details.update({
                "wallet_address": "0x1234567890abcdef"
            })
        
        payment_ctx = main_ctx.create_child_context("process_payment")
        try:
            payment_result = service.process_payment(
                order_id=order_id,
                amount=total,
                payment_method=payment_method,
                payment_details=payment_details,
                ctx=payment_ctx
            )
        except ValueError as e:
            logger.error(
                f"Payment failed for order {order_id}: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'order_process',
                    'order_id': order_id,
                    'payment_method': payment_method,
                    'error': 'payment_failed',
                    'error_detail': str(e)
                }
            )
            return
        
        # 5. Create shipment
        shipping_method = random.choice(shipping_methods)
        
        # Create random shipping address
        shipping_address = {
            "name": "John Doe",
            "street": "123 Main St",
            "city": random.choice(user_locations),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "United States"
        }
        
        shipment_ctx = main_ctx.create_child_context("create_shipment")
        try:
            shipment_result = service.create_shipment(
                order_id=order_id,
                shipping_address=shipping_address,
                items=cart_items,
                shipping_method=shipping_method,
                ctx=shipment_ctx
            )
        except Exception as e:
            logger.error(
                f"Shipment creation failed for order {order_id}: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'order_process',
                    'order_id': order_id,
                    'error': 'shipment_failed',
                    'error_detail': str(e)
                }
            )
            # Don't return; we still want to mark the order as complete
        
        # 6. Mark order as complete
        logger.info(
            f"Order {order_id} process completed successfully",
            extra={
                'correlation_id': correlation_id,
                'span': 'order_process',
                'order_id': order_id,
                'payment_id': payment_result.get('transaction_id'),
                'shipment_id': shipment_result.get('shipment_id') if 'shipment_result' in locals() else None,
                'total_amount': total,
                'status': 'complete'
            }
        )
        
    except Exception as e:
        # Log any unexpected errors
        logger.error(
            f"Unexpected error in order process: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'span': 'order_process',
                'error': 'unexpected_error',
                'error_type': type(e).__name__,
                'error_detail': str(e)
            }
        )

# Run multiple simulations
if __name__ == "__main__":
    logger.info(
        "Starting e-commerce flow simulations",
        extra={
            'simulation_count': 5,
            'simulation_type': 'order_flow'
        }
    )
    
    for i in range(5):
        logger.info(
            f"Running simulation {i+1}/5",
            extra={
                'simulation_number': i+1,
                'simulation_type': 'order_flow'
            }
        )
        simulate_order_process()
        time.sleep(1)  # Pause between simulations
    
    logger.info(
        "All simulations completed",
        extra={
            'simulation_count': 5,
            'simulation_type': 'order_flow',
            'status': 'complete'
        }
    )