import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import EliteAnalystSubscriptionPage from '@/app/[locale]/subscribe/elite-analyst/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/lib/supabase/client', () => ({
  createClient: jest.fn(() => ({
    auth: {
      getSession: jest.fn().mockResolvedValue({
        data: { session: { user: { id: 'test-user-id' } } }
      })
    }
  }))
}))

describe('EliteAnalystSubscriptionPage', () => {
  const mockPush = jest.fn()
  
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    jest.clearAllMocks()
  })

  it('renders subscription page with correct pricing', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    expect(screen.getByText(/\$299/i)).toBeInTheDocument()
    expect(screen.getByText(/Elite Analyst/i)).toBeInTheDocument()
    expect(screen.getByText(/Professional Team Access/i)).toBeInTheDocument()
  })

  it('displays all premium features', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    expect(screen.getByText(/All 7 Markets/i)).toBeInTheDocument()
    expect(screen.getByText(/Unlimited Searches/i)).toBeInTheDocument()
    expect(screen.getByText(/Advanced Analytics/i)).toBeInTheDocument()
    expect(screen.getByText(/TalentPing Alerts/i)).toBeInTheDocument()
    expect(screen.getByText(/API Access/i)).toBeInTheDocument()
    expect(screen.getByText(/Priority Support/i)).toBeInTheDocument()
  })

  it('shows all 7 markets as included', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    const markets = ['South Korea', 'Japan', 'China', 'Thailand', 'Vietnam', 'Philippines', 'India']
    
    markets.forEach(market => {
      expect(screen.getByText(market)).toBeInTheDocument()
    })
  })

  it('validates organization information fields', async () => {
    render(<EliteAnalystSubscriptionPage />)
    
    const submitButton = screen.getByRole('button', { name: /Subscribe to Elite Analyst/i })
    
    // Submit without filling required fields
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  it('requires organization name and use case', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    const orgInput = screen.getByPlaceholderText(/Company Name/i)
    const useCaseSelect = screen.getByRole('combobox')
    
    expect(orgInput).toHaveAttribute('required')
    expect(useCaseSelect).toHaveAttribute('required')
  })

  it('submits form with organization data', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ paymentUrl: 'https://payment.test' })
    })
    
    render(<EliteAnalystSubscriptionPage />)
    
    // Fill organization form
    fireEvent.change(screen.getByPlaceholderText(/John Doe/i), {
      target: { value: 'CEO Name' }
    })
    fireEvent.change(screen.getByPlaceholderText(/john@company.com/i), {
      target: { value: 'ceo@company.com' }
    })
    fireEvent.change(screen.getByPlaceholderText(/Company Name/i), {
      target: { value: 'Test Corp' }
    })
    
    // Select use case
    const useCaseSelect = screen.getByRole('combobox')
    fireEvent.change(useCaseSelect, {
      target: { value: 'professional-scouting' }
    })
    
    // Accept terms
    const termsCheckbox = screen.getByRole('checkbox', { name: /Terms of Service/i })
    fireEvent.click(termsCheckbox)
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /Subscribe to Elite Analyst/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/payment/create',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('elite-analyst')
        })
      )
    })
  })

  it('includes all markets in subscription data', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ paymentUrl: 'https://payment.test' })
    })
    
    render(<EliteAnalystSubscriptionPage />)
    
    // Fill minimal required fields and submit
    fireEvent.change(screen.getByPlaceholderText(/John Doe/i), {
      target: { value: 'Test User' }
    })
    fireEvent.change(screen.getByPlaceholderText(/john@company.com/i), {
      target: { value: 'test@test.com' }
    })
    fireEvent.change(screen.getByPlaceholderText(/Company Name/i), {
      target: { value: 'Test Co' }
    })
    
    const useCaseSelect = screen.getByRole('combobox')
    fireEvent.change(useCaseSelect, { target: { value: 'professional-scouting' } })
    
    const termsCheckbox = screen.getByRole('checkbox', { name: /Terms of Service/i })
    fireEvent.click(termsCheckbox)
    
    const submitButton = screen.getByRole('button', { name: /Subscribe to Elite Analyst/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      const callArgs = (global.fetch as jest.Mock).mock.calls[0][1]
      const body = JSON.parse(callArgs.body)
      
      expect(body.markets).toEqual(['KR', 'JP', 'CN', 'TH', 'VN', 'PH', 'IN'])
    })
  })

  it('displays trust signals', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    expect(screen.getByText(/Secure Payment/i)).toBeInTheDocument()
    expect(screen.getByText(/Cancel Anytime/i)).toBeInTheDocument()
    expect(screen.getByText(/Instant Access/i)).toBeInTheDocument()
  })

  it('shows expected search volume options', () => {
    render(<EliteAnalystSubscriptionPage />)
    
    const searchVolumeSelect = screen.getByLabelText(/Expected Monthly Searches/i)
    
    expect(searchVolumeSelect).toBeInTheDocument()
    fireEvent.click(searchVolumeSelect)
    
    expect(screen.getByText(/200\+ searches/i)).toBeInTheDocument()
    expect(screen.getByText(/500\+ searches/i)).toBeInTheDocument()
    expect(screen.getByText(/1,000\+ searches/i)).toBeInTheDocument()
    expect(screen.getByText(/Unlimited usage/i)).toBeInTheDocument()
  })
})
