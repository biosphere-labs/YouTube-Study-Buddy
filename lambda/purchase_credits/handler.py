"""
Lambda handler for creating Stripe payment intent.

This function handles credit purchase requests:
1. Validates credit package and amount
2. Creates Stripe payment intent
3. Returns client_secret for frontend to complete payment
4. Payment completion is handled by stripe_webhook handler

API Gateway Integration:
- Method: POST
- Path: /credits/purchase
- Authorization: Cognito User Pool
- Request body: { "package": "basic" | "standard" | "premium" }
- Response: { "client_secret": "pi_xxx_secret_xxx", "amount": 999 }
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import (
    success_response,
    error_response,
    extract_user_id_from_event,
    get_item,
    USERS_TABLE
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# Credit packages
CREDIT_PACKAGES = {
    'basic': {
        'credits': 10,
        'price': 999,  # $9.99 in cents
        'description': 'Basic Package - 10 Credits'
    },
    'standard': {
        'credits': 25,
        'price': 1999,  # $19.99 in cents
        'description': 'Standard Package - 25 Credits'
    },
    'premium': {
        'credits': 50,
        'price': 2999,  # $29.99 in cents
        'description': 'Premium Package - 50 Credits'
    }
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle credit purchase request.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        API Gateway response with Stripe client_secret or error

    Example Event:
        {
            "body": "{\"package\": \"standard\"}",
            "headers": {"Authorization": "Bearer <jwt_token>"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123", "email": "user@example.com"}
                }
            }
        }

    Example Response (Success):
        {
            "statusCode": 200,
            "body": {
                "client_secret": "pi_1234567890_secret_abcdefgh",
                "amount": 1999,
                "credits": 25,
                "package": "standard"
            }
        }
    """
    try:
        logger.info(f"Received purchase credits request: {json.dumps(event)}")

        # Extract user ID from JWT token
        user_id = extract_user_id_from_event(event)
        if not user_id:
            logger.warning("Unauthorized request - missing or invalid token")
            return error_response(401, "Unauthorized - Invalid or missing authentication token")

        # Get user email from claims
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_email = claims.get('email', 'unknown@example.com')

        logger.info(f"Processing purchase for user: {user_id} ({user_email})")

        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return error_response(400, "Invalid JSON in request body")

        # Get package
        package = body.get('package', '').lower()
        if package not in CREDIT_PACKAGES:
            logger.warning(f"Invalid package: {package}")
            return error_response(400, f"Invalid package. Must be one of: {', '.join(CREDIT_PACKAGES.keys())}",
                                details={'valid_packages': list(CREDIT_PACKAGES.keys())})

        package_info = CREDIT_PACKAGES[package]
        logger.info(f"Package selected: {package} - {package_info['credits']} credits for ${package_info['price']/100:.2f}")

        # Import Stripe (lazy import to keep cold start fast)
        try:
            import stripe
        except ImportError:
            logger.error("Stripe library not available")
            return error_response(500, "Payment processing unavailable")

        # Configure Stripe
        stripe.api_key = STRIPE_SECRET_KEY

        # Create Stripe payment intent
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=package_info['price'],
                currency='usd',
                metadata={
                    'user_id': user_id,
                    'package': package,
                    'credits': package_info['credits']
                },
                description=package_info['description'],
                receipt_email=user_email
            )

            logger.info(f"Created Stripe payment intent: {payment_intent.id}")

            # Return client_secret for frontend
            return success_response({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': package_info['price'],
                'credits': package_info['credits'],
                'package': package,
                'description': package_info['description']
            })

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}", exc_info=True)
            return error_response(500, "Failed to create payment intent",
                                details={'stripe_error': str(e)})

    except Exception as e:
        logger.error(f"Error processing purchase: {e}", exc_info=True)
        return error_response(500, "Internal server error",
                            details={'error': str(e)})


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "body": json.dumps({"package": "standard"}),
        "headers": {"Authorization": "Bearer test_token"},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test_user_123",
                    "email": "test@example.com"
                }
            }
        }
    }

    # Mock context
    class Context:
        request_id = "test-request-id"
        function_name = "purchase-credits"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
