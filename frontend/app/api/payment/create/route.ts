import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/payment/create
 * Create payment order (Razorpay for India, Stripe for others)
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { amount, currency, userId, email, region, paymentMethod, metadata } = body;

    // Validate input
    if (!amount || !userId || !email || !region) {
      return NextResponse.json(
        { success: false, error_message: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Call Python backend payment service
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/payment/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        amount,
        currency,
        user_id: userId,
        email,
        region,
        payment_method: paymentMethod,
        metadata
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error_message: data.detail || 'Payment creation failed' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Payment creation error:', error);
    return NextResponse.json(
      { success: false, error_message: 'Internal server error' },
      { status: 500 }
    );
  }
}
