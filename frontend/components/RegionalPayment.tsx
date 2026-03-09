"use client";

import React, { useState, useEffect } from 'react';
import { useRegion } from '@/hooks/useRegion';
import Script from 'next/script';

interface RegionalPaymentProps {
  amount: number; // in USD
  userId: string;
  userEmail: string;
  productDescription: string;
  onSuccess?: (paymentId: string) => void;
  onError?: (error: string) => void;
}

declare global {
  interface Window {
    Razorpay: any;
    Stripe: any;
  }
}

/**
 * Regional Payment Component
 * - India: Razorpay with UPI (80% of transactions)
 * - Korea/Japan/Global: Stripe with Apple Pay, Google Pay, KakaoPay
 */
export default function RegionalPayment({
  amount,
  userId,
  userEmail,
  productDescription,
  onSuccess,
  onError
}: RegionalPaymentProps) {
  const { region } = useRegion();
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<string>('');
  const [razorpayLoaded, setRazorpayLoaded] = useState(false);
  const [stripeLoaded, setStripeLoaded] = useState(false);

  const isIndia = region.toLowerCase() === 'india';
  const isKorea = region.toLowerCase() === 'korea';

  // Currency display
  const getCurrencyDisplay = () => {
    const rates: Record<string, { rate: number; symbol: string; currency: string }> = {
      'india': { rate: 83, symbol: '₹', currency: 'INR' },
      'korea': { rate: 1330, symbol: '₩', currency: 'KRW' },
      'japan': { rate: 148, symbol: '¥', currency: 'JPY' },
      'global': { rate: 1, symbol: '$', currency: 'USD' }
    };

    const config = rates[region.toLowerCase()] || rates['global'];
    const localAmount = amount * config.rate;
    
    return {
      display: `${config.symbol}${Math.round(localAmount).toLocaleString()}`,
      amount: localAmount,
      currency: config.currency
    };
  };

  const currencyInfo = getCurrencyDisplay();

  // Initialize payment
  const handlePayment = async () => {
    setIsProcessing(true);

    try {
      // Create payment order
      const response = await fetch('/api/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount,
          currency: currencyInfo.currency,
          userId,
          email: userEmail,
          region,
          paymentMethod,
          metadata: {
            product: productDescription
          }
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error_message || 'Payment creation failed');
      }

      // Route to appropriate payment gateway
      if (isIndia) {
        await processRazorpayPayment(data);
      } else {
        await processStripePayment(data);
      }

    } catch (error) {
      console.error('Payment error:', error);
      onError?.(error instanceof Error ? error.message : 'Payment failed');
      setIsProcessing(false);
    }
  };

  // Razorpay Payment (India)
  const processRazorpayPayment = async (orderData: any) => {
    if (!window.Razorpay) {
      onError?.('Razorpay not loaded');
      setIsProcessing(false);
      return;
    }

    const options = {
      key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
      amount: orderData.amount,
      currency: 'INR',
      name: 'GameRadar',
      description: productDescription,
      order_id: orderData.order_id,
      prefill: {
        email: userEmail
      },
      theme: {
        color: '#F37254'
      },
      handler: async function (response: any) {
        // Verify payment on backend
        try {
          const verifyResponse = await fetch('/api/payment/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              gateway: 'razorpay',
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              userId
            })
          });

          const verifyData = await verifyResponse.json();

          if (verifyData.success) {
            onSuccess?.(response.razorpay_payment_id);
          } else {
            onError?.('Payment verification failed');
          }
        } catch (error) {
          onError?.('Payment verification error');
        } finally {
          setIsProcessing(false);
        }
      },
      modal: {
        ondismiss: function() {
          setIsProcessing(false);
        }
      }
    };

    const razorpay = new window.Razorpay(options);
    razorpay.open();
  };

  // Stripe Payment (Global/Korea/Japan)
  const processStripePayment = async (paymentData: any) => {
    if (!window.Stripe) {
      onError?.('Stripe not loaded');
      setIsProcessing(false);
      return;
    }

    const stripe = window.Stripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY);

    // For this example, redirect to Stripe Checkout
    // In production, you'd use Stripe Elements for embedded form
    const { error } = await stripe.redirectToCheckout({
      sessionId: paymentData.session_id
    });

    if (error) {
      onError?.(error.message || 'Stripe error');
      setIsProcessing(false);
    }
  };

  return (
    <>
      {/* Load Razorpay for India */}
      {isIndia && (
        <Script
          src="https://checkout.razorpay.com/v1/checkout.js"
          onLoad={() => setRazorpayLoaded(true)}
        />
      )}

      {/* Load Stripe for others */}
      {!isIndia && (
        <Script
          src="https://js.stripe.com/v3/"
          onLoad={() => setStripeLoaded(true)}
        />
      )}

      <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
        {/* Payment Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {isIndia ? '💳 Complete Payment' : '💼 Secure Checkout'}
          </h2>
          <p className="text-gray-600">{productDescription}</p>
        </div>

        {/* Amount Display */}
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-6 rounded-lg mb-6">
          <div className="text-center">
            <p className="text-white text-sm mb-1">Amount to Pay</p>
            <p className="text-white text-4xl font-bold">{currencyInfo.display}</p>
            {currencyInfo.currency !== 'USD' && (
              <p className="text-blue-100 text-sm mt-2">≈ ${amount} USD</p>
            )}
          </div>
        </div>

        {/* Payment Methods - India (Razorpay) */}
        {isIndia && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              Select Payment Method
            </h3>
            
            {/* UPI - Highlighted for India */}
            <div 
              onClick={() => setPaymentMethod('upi')}
              className={`border-2 rounded-lg p-4 mb-3 cursor-pointer transition-all ${
                paymentMethod === 'upi' 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-300 hover:border-green-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-xl mr-3">
                    UPI
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">UPI Payment</p>
                    <p className="text-sm text-gray-600">Google Pay, PhonePe, Paytm</p>
                  </div>
                </div>
                <div>
                  {paymentMethod === 'upi' && (
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                  <span className="ml-2 px-2 py-1 bg-orange-500 text-white text-xs rounded-full">
                    FASTEST
                  </span>
                </div>
              </div>
            </div>

            {/* Other Razorpay methods */}
            <div 
              onClick={() => setPaymentMethod('card')}
              className={`border-2 rounded-lg p-4 mb-3 cursor-pointer transition-all ${
                paymentMethod === 'card' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-blue-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="text-3xl mr-3">💳</div>
                  <div>
                    <p className="font-semibold text-gray-900">Debit/Credit Card</p>
                    <p className="text-sm text-gray-600">Visa, Mastercard, RuPay</p>
                  </div>
                </div>
                {paymentMethod === 'card' && (
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </div>

            <div 
              onClick={() => setPaymentMethod('netbanking')}
              className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                paymentMethod === 'netbanking' 
                  ? 'border-purple-500 bg-purple-50' 
                  : 'border-gray-300 hover:border-purple-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="text-3xl mr-3">🏦</div>
                  <div>
                    <p className="font-semibold text-gray-900">Net Banking</p>
                    <p className="text-sm text-gray-600">All major banks</p>
                  </div>
                </div>
                {paymentMethod === 'netbanking' && (
                  <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Payment Methods - Global (Stripe) */}
        {!isIndia && (
          <div className="mb-6 space-y-3">
            <div className="flex items-center justify-center space-x-4 py-4">
              <div className="text-2xl">💳</div>
              <div className="text-2xl">🍎</div>
              <div className="text-2xl">📱</div>
              {isKorea && <div className="text-2xl">🇰🇷</div>}
            </div>
            <p className="text-center text-sm text-gray-600">
              {isKorea 
                ? 'Card, Apple Pay, Google Pay, KakaoPay'
                : 'Card, Apple Pay, Google Pay'
              }
            </p>
          </div>
        )}

        {/* Pay Button */}
        <button
          onClick={handlePayment}
          disabled={isProcessing || (isIndia && !paymentMethod) || (isIndia && !razorpayLoaded) || (!isIndia && !stripeLoaded)}
          className={`w-full py-4 rounded-lg font-bold text-lg transition-all ${
            isProcessing || (isIndia && !paymentMethod)
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : isIndia
              ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white hover:shadow-xl'
              : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-xl'
          }`}
        >
          {isProcessing ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Processing...
            </span>
          ) : (
            <>
              {isIndia ? '🔒 Pay Securely' : '🔐 Proceed to Checkout'}
            </>
          )}
        </button>

        {/* Security Badge */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            🔒 Secure payment powered by {isIndia ? 'Razorpay' : 'Stripe'}
          </p>
        </div>
      </div>
    </>
  );
}
