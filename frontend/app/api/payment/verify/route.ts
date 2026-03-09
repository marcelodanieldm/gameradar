import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/payment/verify
 * Verify payment completion (Razorpay signature or Stripe payment intent)
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gateway, userId } = body;

    // Validate input
    if (!gateway || !userId) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Call Python backend payment verification service
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/payment/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.detail || 'Payment verification failed' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Payment verification error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
