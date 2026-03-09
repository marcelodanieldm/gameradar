"""
Payment Gateway Service - Regional Payment Architecture
Handles Razorpay (India/UPI) and Stripe (Korea/Japan/Global)
"""
import os
from typing import Dict, Optional, Literal
from datetime import datetime
import razorpay
import stripe
from pydantic import BaseModel


class PaymentRequest(BaseModel):
    """Payment request model"""
    amount: float  # in USD
    currency: str
    user_id: str
    email: str
    region: Literal["india", "korea", "japan", "global"]
    payment_method: Optional[str] = None  # upi, card, kakao_pay, etc.
    metadata: Optional[Dict] = None


class PaymentResponse(BaseModel):
    """Payment response model"""
    success: bool
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_url: Optional[str] = None
    error_message: Optional[str] = None
    gateway: str


class PaymentGatewayService:
    """
    Regional Payment Gateway Service
    - India: Razorpay with UPI (80% of digital transactions)
    - Korea/Japan/Global: Stripe with Apple Pay, Google Pay, KakaoPay
    """
    
    def __init__(self):
        # Razorpay Setup (India)
        self.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
        self.razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.razorpay_client = None
        
        if self.razorpay_key_id and self.razorpay_key_secret:
            self.razorpay_client = razorpay.Client(
                auth=(self.razorpay_key_id, self.razorpay_key_secret)
            )
        
        # Stripe Setup (Global)
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
        
        # Currency conversion rates (simplified - use real-time API in production)
        self.currency_rates = {
            "INR": 83.0,  # 1 USD = 83 INR
            "KRW": 1330.0,  # 1 USD = 1330 KRW
            "JPY": 148.0,  # 1 USD = 148 JPY
            "USD": 1.0
        }
    
    def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Route payment to appropriate gateway based on region
        """
        if payment_request.region == "india":
            return self._create_razorpay_payment(payment_request)
        else:
            return self._create_stripe_payment(payment_request)
    
    def _create_razorpay_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create Razorpay payment order (India)
        Supports UPI, Cards, Wallets, NetBanking
        """
        try:
            if not self.razorpay_client:
                return PaymentResponse(
                    success=False,
                    error_message="Razorpay not configured",
                    gateway="razorpay"
                )
            
            # Convert to INR
            amount_inr = int(payment_request.amount * self.currency_rates["INR"] * 100)  # in paise
            
            # Create Razorpay Order
            order_data = {
                "amount": amount_inr,
                "currency": "INR",
                "receipt": f"order_{payment_request.user_id}_{int(datetime.now().timestamp())}",
                "notes": {
                    "user_id": payment_request.user_id,
                    "email": payment_request.email,
                    **(payment_request.metadata or {})
                }
            }
            
            order = self.razorpay_client.order.create(data=order_data)
            
            return PaymentResponse(
                success=True,
                order_id=order["id"],
                payment_url=None,  # Frontend will handle Razorpay checkout
                gateway="razorpay"
            )
            
        except Exception as e:
            return PaymentResponse(
                success=False,
                error_message=str(e),
                gateway="razorpay"
            )
    
    def _create_stripe_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create Stripe payment intent (Korea/Japan/Global)
        Supports Apple Pay, Google Pay, KakaoPay, Cards
        """
        try:
            if not self.stripe_api_key:
                return PaymentResponse(
                    success=False,
                    error_message="Stripe not configured",
                    gateway="stripe"
                )
            
            # Determine currency based on region
            currency_map = {
                "korea": "KRW",
                "japan": "JPY",
                "global": "USD"
            }
            currency = currency_map.get(payment_request.region, "USD")
            
            # Convert amount
            amount_cents = int(
                payment_request.amount * 
                self.currency_rates[currency] * 
                (1 if currency == "JPY" else 100)  # JPY doesn't use decimals
            )
            
            # Create Stripe Payment Intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer_email=payment_request.email,
                metadata={
                    "user_id": payment_request.user_id,
                    "region": payment_request.region,
                    **(payment_request.metadata or {})
                },
                payment_method_types=[
                    "card",
                    "apple_pay",
                    "google_pay",
                    **(["kakao_pay"] if payment_request.region == "korea" else [])
                ]
            )
            
            return PaymentResponse(
                success=True,
                payment_id=payment_intent.id,
                payment_url=None,  # Frontend will handle Stripe Elements
                gateway="stripe"
            )
            
        except Exception as e:
            return PaymentResponse(
                success=False,
                error_message=str(e),
                gateway="stripe"
            )
    
    def verify_razorpay_payment(
        self, 
        razorpay_order_id: str, 
        razorpay_payment_id: str, 
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        """
        try:
            if not self.razorpay_client:
                return False
            
            self.razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            return True
        except:
            return False
    
    def verify_stripe_payment(self, payment_intent_id: str) -> bool:
        """
        Verify Stripe payment completion
        """
        try:
            if not self.stripe_api_key:
                return False
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent.status == "succeeded"
        except:
            return False


# Singleton instance
payment_gateway = PaymentGatewayService()
