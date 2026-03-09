import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/talent-ping/subscribe
 * Subscribe user to Talent-Ping alerts
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId, region, channels, whatsappNumber, telegramId, email, alertFrequency } = body;

    // Validate input
    if (!userId || !region || !channels || channels.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Validate channel-specific data
    if (channels.includes('whatsapp') && !whatsappNumber) {
      return NextResponse.json(
        { success: false, error: 'WhatsApp number required' },
        { status: 400 }
      );
    }

    if (channels.includes('telegram') && !telegramId) {
      return NextResponse.json(
        { success: false, error: 'Telegram ID required' },
        { status: 400 }
      );
    }

    if (channels.includes('email') && !email) {
      return NextResponse.json(
        { success: false, error: 'Email required' },
        { status: 400 }
      );
    }

    // Call Python backend subscription service
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/talent-ping/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        region,
        notification_channels: channels,
        whatsapp_number: whatsappNumber,
        telegram_id: telegramId,
        email,
        alert_frequency: alertFrequency || 'instant'
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.detail || 'Subscription failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true, subscription: data });

  } catch (error) {
    console.error('Subscription error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/talent-ping/subscribe
 * Get user's subscription preferences
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID required' },
        { status: 400 }
      );
    }

    // Call Python backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/talent-ping/subscribe?user_id=${userId}`);

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.detail || 'Failed to fetch subscription' },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true, subscription: data });

  } catch (error) {
    console.error('Fetch subscription error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/talent-ping/subscribe
 * Unsubscribe from Talent-Ping alerts
 */
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return NextResponse.json(
        { success: false, error: 'User ID required' },
        { status: 400 }
      );
    }

    // Call Python backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(
      `${backendUrl}/api/talent-ping/subscribe?user_id=${userId}`,
      { method: 'DELETE' }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: data.detail || 'Unsubscribe failed' },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true, message: 'Unsubscribed successfully' });

  } catch (error) {
    console.error('Unsubscribe error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
