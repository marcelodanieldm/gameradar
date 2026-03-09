# Sprint 3: Quick Reference Guide 🚀

## 🎯 Quick Start (5 Minutes)

### 1. Run Setup Script
```bash
# Windows
setup_sprint3.bat

# Linux/Mac
chmod +x setup_sprint3.sh
./setup_sprint3.sh
```

### 2. Configure Keys
Edit `.env` and add your API keys:
- Razorpay: [Get Key](https://dashboard.razorpay.com/app/keys)
- Stripe: [Get Key](https://dashboard.stripe.com/apikeys)
- WhatsApp: [Get Token](https://developers.facebook.com/apps/)
- Telegram: [Get Bot Token](https://t.me/BotFather)

### 3. Start Servers
```bash
# Terminal 1 - Backend
python api_routes_sprint3.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### 4. Test It!
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Payment Test Page: http://localhost:3000/payment-test

---

## 💳 Payment Integration

### India (Razorpay + UPI)
```tsx
import RegionalPayment from '@/components/RegionalPayment';

<RegionalPayment
  amount={49.99}
  userId="user123"
  userEmail="user@example.com"
  region="india"  // Auto-selects Razorpay
  productDescription="Premium Subscription"
/>
```

**Test Cards:**
- Card: `4111 1111 1111 1111`
- UPI: `success@razorpay`

### Global (Stripe)
```tsx
<RegionalPayment
  amount={49.99}
  userId="user123"
  userEmail="user@example.com"
  region="korea"  // Auto-selects Stripe
  productDescription="Premium Subscription"
/>
```

**Test Card:**
- Card: `4242 4242 4242 4242`

---

## 🔔 Talent-Ping Alerts

### Subscribe to Alerts
```tsx
import TalentPingSubscription from '@/components/TalentPingSubscription';

<TalentPingSubscription
  userId="user123"
  onSubscribe={(data) => console.log('Subscribed!', data)}
/>
```

### Send Alert (Backend)
```python
from notification_service import talent_ping_service
from notification_service import NotificationPreference, PlayerAlert

# Get user preferences
preference = NotificationPreference(
    user_id="user123",
    region="india",
    whatsapp_number="+919876543210",
    notification_channels=["whatsapp", "email"]
)

# Create alert
alert = PlayerAlert(
    player_name="João Silva",
    player_position="Mid Laner",
    player_age=19,
    similarity_score=0.945,
    key_stats={
        "KDA": 4.8,
        "CS/Min": 9.2,
        "Win Rate": 67.0
    },
    profile_url="player/joao-silva-123",
    region="india"
)

# Send
await talent_ping_service.send_talent_alert(preference, alert)
```

---

## 🌍 Regional Customization

### Payment Methods by Region

| Region | Gateway | Methods |
|--------|---------|---------|
| 🇮🇳 India | Razorpay | UPI, Card, NetBanking |
| 🇰🇷 Korea | Stripe | Card, KakaoPay, Apple Pay |
| 🇯🇵 Japan | Stripe | Card, Apple Pay, Google Pay |
| 🌎 Global | Stripe | Card, Apple Pay, Google Pay |

### Notification Channels by Region

| Region | Primary | Secondary | Format |
|--------|---------|-----------|--------|
| 🇮🇳 India | WhatsApp | Telegram | FOMO, Emojis |
| 🇻🇳 Vietnam | WhatsApp | Telegram | FOMO, Emojis |
| 🇰🇷 Korea | Email + PDF | In-App | Professional |
| 🇯🇵 Japan | Email + PDF | In-App | Professional |
| 🇨🇳 China | Email + PDF | In-App | Professional |

---

## 📡 API Endpoints Cheatsheet

### Payment APIs
```bash
# Create payment
POST /api/payment/create
{
  "amount": 49.99,
  "region": "india",
  "user_id": "user123",
  "email": "user@example.com"
}

# Verify payment
POST /api/payment/verify
{
  "gateway": "razorpay",
  "user_id": "user123",
  "razorpay_order_id": "order_xyz",
  "razorpay_payment_id": "pay_xyz",
  "razorpay_signature": "signature_xyz"
}
```

### Talent-Ping APIs
```bash
# Subscribe
POST /api/talent-ping/subscribe
{
  "user_id": "user123",
  "region": "india",
  "notification_channels": ["whatsapp", "telegram"],
  "whatsapp_number": "+919876543210"
}

# Get subscription
GET /api/talent-ping/subscribe?userId=user123

# Unsubscribe
DELETE /api/talent-ping/subscribe?userId=user123

# Send alert (backend only)
POST /api/talent-ping/send-alert
{
  "user_id": "user123",
  "player_name": "João Silva",
  "similarity_score": 0.945,
  ...
}
```

---

## 🗄️ Database Queries

### Get Payment Stats by Region
```sql
SELECT 
    region,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
    SUM(amount) as total_revenue
FROM payment_transactions
GROUP BY region
ORDER BY total_revenue DESC;
```

### Get Active Talent-Ping Subscribers
```sql
SELECT 
    region,
    COUNT(*) as total_subscribers,
    notification_channels,
    COUNT(*) as channel_count
FROM talent_ping_subscriptions
WHERE is_active = true
GROUP BY region, notification_channels;
```

### Get Alert Engagement Metrics
```sql
SELECT 
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened,
    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
    ROUND(COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as open_rate,
    ROUND(COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as click_rate
FROM talent_ping_alerts
WHERE sent_at >= NOW() - INTERVAL '7 days';
```

---

## 🧪 Testing Commands

### Test Razorpay Payment
```bash
curl -X POST http://localhost:8000/api/payment/create \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 49.99,
    "currency": "USD",
    "user_id": "test_user",
    "email": "test@example.com",
    "region": "india"
  }'
```

### Test WhatsApp Alert
```python
python -c "
import asyncio
from notification_service import talent_ping_service, NotificationPreference, PlayerAlert

async def test():
    pref = NotificationPreference(
        user_id='test',
        region='india',
        whatsapp_number='+919876543210',
        notification_channels=['whatsapp']
    )
    alert = PlayerAlert(
        player_name='Test Player',
        player_position='Mid',
        player_age=20,
        similarity_score=0.95,
        key_stats={'KDA': 5.0},
        profile_url='test',
        region='india'
    )
    result = await talent_ping_service.send_talent_alert(pref, alert)
    print(result)

asyncio.run(test())
"
```

---

## 🐛 Common Issues

### "Razorpay not configured"
→ Check `.env` has `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`

### "WhatsApp delivery failed"
→ Verify `WHATSAPP_BUSINESS_TOKEN` and phone number format: `+[country][number]`

### "Payment verification failed"
→ Check webhook signature in production, use test credentials in dev

### "Database connection error"
→ Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

---

## 📚 Resources

- **Full Documentation**: [SPRINT3_CASHFLOW_ENGAGEMENT.md](SPRINT3_CASHFLOW_ENGAGEMENT.md)
- **Razorpay Docs**: https://razorpay.com/docs/
- **Stripe Docs**: https://stripe.com/docs
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## 🆘 Getting Help

1. Check [SPRINT3_CASHFLOW_ENGAGEMENT.md](SPRINT3_CASHFLOW_ENGAGEMENT.md) for detailed docs
2. Review API logs: `api_routes_sprint3.py` outputs errors
3. Test in Postman/Insomnia using examples above
4. Check Supabase logs for database issues

---

**Happy Coding! 🚀**
