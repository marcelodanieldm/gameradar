import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EliteAnalystDashboard from '@/components/EliteAnalystDashboard'

jest.mock('@/lib/supabase/client', () => ({
  createClient: jest.fn(() => ({
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          single: jest.fn().mockResolvedValue({
            data: {
              searches_count: 150,
              current_period_end: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
              alerts_active: 5,
              api_calls_today: 1200,
              last_search_at: new Date().toISOString()
            }
          })
        }))
      }))
    }))
  }))
}))

describe('EliteAnalystDashboard', () => {
  const mockProps = {
    userId: 'test-user-id',
    initialStats: {
      searchesCount: 150,
      daysRemaining: 20,
      alertsActive: 5,
      apiCallsToday: 1200
    },
    selectedMarkets: ['KR', 'JP', 'CN', 'TH', 'VN', 'PH', 'IN']
  }

  it('renders dashboard with correct title', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Advanced Dashboard/i)).toBeInTheDocument()
    expect(screen.getByText(/ELITE ANALYST/i)).toBeInTheDocument()
  })

  it('displays all key statistics', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText('150')).toBeInTheDocument() // Searches
    expect(screen.getByText('5')).toBeInTheDocument() // Active alerts
    expect(screen.getByText('1,200')).toBeInTheDocument() // API calls
    expect(screen.getByText('7/7')).toBeInTheDocument() // Markets
  })

  it('shows subscription status as active', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Active/i)).toBeInTheDocument()
    expect(screen.getByText(/20 days remaining/i)).toBeInTheDocument()
  })

  it('displays all 7 markets', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    const markets = [
      'South Korea',
      'Japan', 
      'China',
      'Thailand',
      'Vietnam',
      'Philippines',
      'India'
    ]
    
    markets.forEach(market => {
      expect(screen.getByText(market)).toBeInTheDocument()
    })
  })

  it('has 4 navigation tabs', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Overview/i)).toBeInTheDocument()
    expect(screen.getByText(/Advanced Analytics/i)).toBeInTheDocument()
    expect(screen.getByText(/TalentPing Alerts/i)).toBeInTheDocument()
    expect(screen.getByText(/API Access/i)).toBeInTheDocument()
  })

  it('switches between tabs correctly', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    // Click Analytics tab
    const analyticsTab = screen.getByText(/Advanced Analytics/i)
    fireEvent.click(analyticsTab)
    
    // Should show analytics content
    waitFor(() => {
      expect(screen.getByText(/AI-Powered Recommendations/i)).toBeInTheDocument()
    })
  })

  it('shows unlimited searches label', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Unlimited usage/i)).toBeInTheDocument()
  })

  it('displays real-time monitoring badge', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Real-time monitoring/i)).toBeInTheDocument()
  })

  it('shows integration active status for API', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/Integration active/i)).toBeInTheDocument()
  })

  it('updates stats periodically', async () => {
    jest.useFakeTimers()
    
    const mockFetch = jest.fn().mockResolvedValue({
      data: {
        searches_count: 200, // Updated value
        current_period_end: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
        alerts_active: 6,
        api_calls_today: 1500
      }
    })
    
    jest.spyOn(require('@/lib/supabase/client'), 'createClient').mockReturnValue({
      from: jest.fn(() => ({
        select: jest.fn(() => ({
          eq: jest.fn(() => ({
            single: mockFetch
          }))
        }))
      }))
    })
    
    render(<EliteAnalystDashboard {...mockProps} />)
    
    // Fast-forward 30 seconds
    jest.advanceTimersByTime(30000)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
    })
    
    jest.useRealTimers()
  })

  it('displays quick action cards', () => {
    render(<EliteAnalystDashboard {...mockProps} />)
    
    expect(screen.getByText(/View Analytics/i)).toBeInTheDocument()
    expect(screen.getByText(/Set Alerts/i)).toBeInTheDocument()
    expect(screen.getByText(/Export Reports/i)).toBeInTheDocument()
  })
})
