"""
Lambda handler for Stripe webhook events.

This function handles Stripe webhook events:
1. Verifies webhook signature for security
2. Handles payment_intent.succeeded event
3. Adds credits to user account
4. Creates credit transaction record
5. Implements idempotent handling to prevent duplicate credits

Webhook Configuration:
- Endpoint: /webhooks/stripe
- Events: payment_intent.succeeded
- Signature verification: Required (STRIPE_WEBHOOK_SECRET)
- No authorization required (webhook signature provides security)
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
    add_credits
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


def handle_payment_success(payment_intent: Dict[str, Any]) -> bool:
    """
    Handle successful payment event.

    Args:
        payment_intent: Stripe PaymentIntent object

    Returns:
        True if credits were added successfully

    Raises:
        Exception if processing fails
    """
    payment_intent_id = payment_intent.get('id')
    metadata = payment_intent.get('metadata', {})

    user_id = metadata.get('user_id')
    package = metadata.get('package')
    credits = int(metadata.get('credits', 0))

    logger.info(f"Processing payment success: {payment_intent_id}")
    logger.info(f"User: {user_id}, Package: {package}, Credits: {credits}")

    if not user_id or not credits:
        logger.error(f"Missing metadata in payment intent: {payment_intent_id}")
        raise ValueError("Missing user_id or credits in payment metadata")

    # Add credits to user account (idempotent)
    # Transaction ID is the payment_intent_id for idempotency
    add_credits(
        user_id=user_id,
        amount=credits,
        transaction_id=payment_intent_id,
        reason=f'purchase_{package}'
    )

    logger.info(f"Successfully added {credits} credits to user {user_id}")
    return True


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle Stripe webhook event.

    Args:
        event: API Gateway event containing webhook data
        context: Lambda context object

    Returns:
        API Gateway response

    Example Event:
        {
            "body": "{\"id\": \"evt_...\", \"type\": \"payment_intent.succeeded\", ...}",
            "headers": {
                "stripe-signature": "t=1234567890,v1=abc123..."
            }
        }

    Example Response (Success):
        {
            "statusCode": 200,
            "body": "{\"received\": true}"
        }

    Example Response (Error - Invalid Signature):
        {
            "statusCode": 401,
            "body": "{\"error\": \"Invalid webhook signature\"}"
        }
    """
    try:
        logger.info("Received Stripe webhook event")

        # Get request body and signature
        payload = event.get('body', '')
        sig_header = event.get('headers', {}).get('stripe-signature') or \
                    event.get('headers', {}).get('Stripe-Signature')

        if not sig_header:
            logger.error("Missing stripe-signature header")
            return error_response(401, "Missing webhook signature")

        # Import Stripe (lazy import)
        try:
            import stripe
        except ImportError:
            logger.error("Stripe library not available")
            return error_response(500, "Webhook processing unavailable")

        # Configure Stripe
        stripe.api_key = STRIPE_SECRET_KEY

        # Verify webhook signature
        try:
            webhook_event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            logger.info(f"Verified webhook signature - event type: {webhook_event['type']}")
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return error_response(400, "Invalid webhook payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return error_response(401, "Invalid webhook signature")

        # Handle the event
        event_type = webhook_event['type']
        logger.info(f"Processing event: {event_type}")

        if event_type == 'payment_intent.succeeded':
            payment_intent = webhook_event['data']['object']

            try:
                handle_payment_success(payment_intent)
                return success_response({'received': True, 'processed': True})
            except Exception as e:
                logger.error(f"Error handling payment success: {e}", exc_info=True)
                # Return 200 to acknowledge receipt but log the error
                # This prevents Stripe from retrying immediately
                return success_response({
                    'received': True,
                    'processed': False,
                    'error': str(e)
                })

        elif event_type == 'payment_intent.payment_failed':
            payment_intent = webhook_event['data']['object']
            logger.warning(f"Payment failed: {payment_intent.get('id')}")
            # Just acknowledge - no action needed
            return success_response({'received': True})

        else:
            # Unhandled event type
            logger.info(f"Unhandled event type: {event_type}")
            return success_response({'received': True})

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Return 200 to prevent Stripe from retrying
        return success_response({
            'received': True,
            'error': str(e)
        })


# For local testing
if __name__ == "__main__":
    # Test event (simulated webhook)
    test_payload = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "amount": 1999,
                "currency": "usd",
                "metadata": {
                    "user_id": "test_user_123",
                    "package": "standard",
                    "credits": "25"
                }
            }
        }
    }

    test_event = {
        "body": json.dumps(test_payload),
        "headers": {
            "stripe-signature": "t=1234567890,v1=test_signature"
        }
    }

    # Mock context
    class Context:
        request_id = "test-request-id"
        function_name = "stripe-webhook"

    # Note: This will fail signature verification in local testing
    # Use Stripe CLI for proper webhook testing:
    # stripe listen --forward-to localhost:3000/webhooks/stripe
    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
