import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import StreetScoutSubscriptionPage from '@/app/[locale]/subscribe/street-scout/page'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock Supabase client
jest.mock('@/lib/supabase/client', () => ({
  createClient: jest.fn(() => ({
    auth: {
      getSession: jest.fn().mockResolvedValue({
        data: { session: { user: { id: 'test-user-id' } } }
      })
    }
  }))
}))

describe('StreetScoutSubscriptionPage', () => {
  const mockPush = jest.fn()
  
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    jest.clearAllMocks()
  })

  it('renders subscription page with correct pricing', () => {
    render(<StreetScoutSubscriptionPage />)
    
    expect(screen.getByText(/\$99/i)).toBeInTheDocument()
    expect(screen.getByText(/mes/i)).toBeInTheDocument()
    expect(screen.getByText(/Street Scout/i)).toBeInTheDocument()
  })

  it('displays all features correctly', () => {
    render(<StreetScoutSubscriptionPage />)
    
    expect(screen.getByText(/2 mercados/i)).toBeInTheDocument()
    expect(screen.getByText(/50 búsquedas/i)).toBeInTheDocument()
    expect(screen.getByText(/Perfiles detallados/i)).toBeInTheDocument()
    expect(screen.getByText(/Exportar PDF/i)).toBeInTheDocument()
  })

  it('allows selecting exactly 2 markets', () => {
    render(<StreetScoutSubscriptionPage />)
    
    const marketCheckboxes = screen.getAllByRole('checkbox')
    
    // Select first market
    fireEvent.click(marketCheckboxes[0])
    expect(marketCheckboxes[0]).toBeChecked()
    
    // Select second market
    fireEvent.click(marketCheckboxes[1])
    expect(marketCheckboxes[1]).toBeChecked()
    
    // Third market should be disabled
    fireEvent.click(marketCheckboxes[2])
    expect(marketCheckboxes[2]).not.toBeChecked()
  })

  it('validates form fields before submission', async () => {
    render(<StreetScoutSubscriptionPage />)
    
    const submitButton = screen.getByRole('button', { name: /Suscribirse/i })
    
    // Try to submit without filling form
    fireEvent.click(submitButton)
    
    // Form should not submit (HTML5 validation)
    await waitFor(() => {
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  it('submits form with valid data', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ paymentUrl: 'https://payment.test' })
    })
    
    render(<StreetScoutSubscriptionPage />)
    
    // Fill form
    fireEvent.change(screen.getByPlaceholderText(/nombre/i), {
      target: { value: 'Juan Pérez' }
    })
    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'juan@example.com' }
    })
    
    // Select 2 markets
    const marketCheckboxes = screen.getAllByRole('checkbox')
    fireEvent.click(marketCheckboxes[0])
    fireEvent.click(marketCheckboxes[1])
    
    // Accept terms
    const termsCheckbox = screen.getByLabelText(/términos/i)
    fireEvent.click(termsCheckbox)
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /Suscribirse/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/payment/create',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      )
    })
  })

  it('displays loading state during submission', async () => {
    global.fetch = jest.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    )
    
    render(<StreetScoutSubscriptionPage />)
    
    const submitButton = screen.getByRole('button', { name: /Suscribirse/i })
    fireEvent.click(submitButton)
    
    expect(screen.getByText(/Procesando/i)).toBeInTheDocument()
  })

  it('handles payment API errors gracefully', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ error: 'Payment failed' })
    })
    
    render(<StreetScoutSubscriptionPage />)
    
    const submitButton = screen.getByRole('button', { name: /Suscribirse/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Payment failed/i)).toBeInTheDocument()
    })
  })

  it('redirects unauthenticated users to login', async () => {
    // Mock no session
    jest.spyOn(require('@/lib/supabase/client'), 'createClient').mockReturnValue({
      auth: {
        getSession: jest.fn().mockResolvedValue({
          data: { session: null }
        })
      }
    })
    
    render(<StreetScoutSubscriptionPage />)
    
    const submitButton = screen.getByRole('button', { name: /Suscribirse/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })
})
