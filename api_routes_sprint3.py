"""
FastAPI Backend Routes for Payment and Talent-Ping
Sprint 3: Regional Payment Gateways and Notification System
"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal
from datetime import datetime
import os

# Import our services
from payment_gateway import payment_gateway, PaymentRequest, PaymentResponse
from notification_service import (
    talent_ping_service, 
    NotificationPreference, 
    PlayerAlert
)
from supabase_client import supabase

app = FastAPI()


# ============================================================================
# PAYMENT ROUTES
# ============================================================================

class PaymentCreateRequest(BaseModel):
    amount: float
    currency: str
    user_id: str
    email: EmailStr
    region: Literal["india", "korea", "japan", "vietnam", "china", "global"]
    payment_method: Optional[str] = None
    metadata: Optional[dict] = None


class PaymentVerifyRequest(BaseModel):
    gateway: Literal["razorpay", "stripe"]
    user_id: str
    # Razorpay fields
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    # Stripe fields
    payment_intent_id: Optional[str] = None


@app.post("/api/payment/create")
async def create_payment(request: PaymentCreateRequest):
    """
    Create payment order
    Routes to Razorpay (India) or Stripe (Global)
    """
    try:
        payment_request = PaymentRequest(
            amount=request.amount,
            currency=request.currency,
            user_id=request.user_id,
            email=request.email,
            region=request.region,
            payment_method=request.payment_method,
            metadata=request.metadata
        )
        
        response = payment_gateway.create_payment(payment_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error_message)
        
        # Log payment attempt in database
        supabase.table("payment_transactions").insert({
            "user_id": request.user_id,
            "amount": request.amount,
            "currency": request.currency,
            "region": request.region,
            "gateway": response.gateway,
            "order_id": response.order_id,
            "payment_id": response.payment_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        return response.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payment/verify")
async def verify_payment(request: PaymentVerifyRequest):
    """
    Verify payment completion
    """
    try:
        verified = False
        payment_id = None
        
        if request.gateway == "razorpay":
            if not all([request.razorpay_order_id, request.razorpay_payment_id, request.razorpay_signature]):
                raise HTTPException(status_code=400, detail="Missing Razorpay verification fields")
            
            verified = payment_gateway.verify_razorpay_payment(
                request.razorpay_order_id,
                request.razorpay_payment_id,
                request.razorpay_signature
            )
            payment_id = request.razorpay_payment_id
            
        elif request.gateway == "stripe":
            if not request.payment_intent_id:
                raise HTTPException(status_code=400, detail="Missing Stripe payment intent ID")
            
            verified = payment_gateway.verify_stripe_payment(request.payment_intent_id)
            payment_id = request.payment_intent_id
        
        if not verified:
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        # Update payment status in database
        supabase.table("payment_transactions").update({
            "status": "completed",
            "payment_id": payment_id,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("user_id", request.user_id).eq("status", "pending").execute()
        
        # Activate premium features for user
        supabase.table("user_subscriptions").upsert({
            "user_id": request.user_id,
            "subscription_type": "premium",
            "status": "active",
            "activated_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {
            "success": True,
            "payment_id": payment_id,
            "message": "Payment verified successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TALENT-PING SUBSCRIPTION ROUTES
# ============================================================================

class TalentPingSubscribeRequest(BaseModel):
    user_id: str
    region: Literal["india", "vietnam", "korea", "japan", "china", "global"]
    notification_channels: List[Literal["email", "whatsapp", "telegram", "in_app"]]
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    email: Optional[EmailStr] = None
    alert_frequency: Literal["instant", "daily", "weekly"] = "instant"


@app.post("/api/talent-ping/subscribe")
async def subscribe_talent_ping(request: TalentPingSubscribeRequest):
    """
    Subscribe user to Talent-Ping alerts
    """
    try:
        # Validate channel-specific requirements
        if "whatsapp" in request.notification_channels and not request.whatsapp_number:
            raise HTTPException(status_code=400, detail="WhatsApp number required")
        
        if "telegram" in request.notification_channels and not request.telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID required")
        
        if "email" in request.notification_channels and not request.email:
            raise HTTPException(status_code=400, detail="Email required")
        
        # Store subscription in database
        subscription_data = {
            "user_id": request.user_id,
            "region": request.region,
            "notification_channels": request.notification_channels,
            "whatsapp_number": request.whatsapp_number,
            "telegram_id": request.telegram_id,
            "email": request.email,
            "alert_frequency": request.alert_frequency,
            "subscribed_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        result = supabase.table("talent_ping_subscriptions").upsert(
            subscription_data,
            on_conflict="user_id"
        ).execute()
        
        return {
            "success": True,
            "subscription": result.data[0] if result.data else subscription_data,
            "message": f"Successfully subscribed to Talent-Ping via {', '.join(request.notification_channels)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/talent-ping/subscribe")
async def get_talent_ping_subscription(user_id: str):
    """
    Get user's Talent-Ping subscription preferences
    """
    try:
        result = supabase.table("talent_ping_subscriptions").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/talent-ping/subscribe")
async def unsubscribe_talent_ping(user_id: str):
    """
    Unsubscribe from Talent-Ping alerts
    """
    try:
        supabase.table("talent_ping_subscriptions").update({
            "is_active": False,
            "unsubscribed_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()
        
        return {
            "success": True,
            "message": "Successfully unsubscribed from Talent-Ping"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/talent-ping/send-alert")
async def send_talent_alert(
    user_id: str,
    player_name: str,
    player_position: str,
    player_age: int,
    similarity_score: float,
    key_stats: dict,
    profile_url: str
):
    """
    Send talent alert to subscribed user
    This would typically be called by a background job/worker
    """
    try:
        # Get user's subscription preferences
        subscription_result = supabase.table("talent_ping_subscriptions").select("*").eq(
            "user_id", user_id
        ).eq("is_active", True).execute()
        
        if not subscription_result.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        sub_data = subscription_result.data[0]
        
        # Create notification preference and alert
        preference = NotificationPreference(
            user_id=user_id,
            region=sub_data["region"],
            email=sub_data.get("email"),
            whatsapp_number=sub_data.get("whatsapp_number"),
            telegram_id=sub_data.get("telegram_id"),
            notification_channels=sub_data["notification_channels"],
            alert_frequency=sub_data.get("alert_frequency", "instant")
        )
        
        alert = PlayerAlert(
            player_name=player_name,
            player_position=player_position,
            player_age=player_age,
            similarity_score=similarity_score,
            key_stats=key_stats,
            profile_url=profile_url,
            region=sub_data["region"]
        )
        
        # Send notifications
        results = await talent_ping_service.send_talent_alert(preference, alert)
        
        # Log alert in database
        supabase.table("talent_ping_alerts").insert({
            "user_id": user_id,
            "player_name": player_name,
            "channels_sent": list(results.keys()),
            "delivery_status": results,
            "sent_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {
            "success": True,
            "delivery_status": results,
            "message": "Alert sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
