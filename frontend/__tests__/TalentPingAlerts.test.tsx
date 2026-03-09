import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TalentPingAlerts from '@/components/TalentPingAlerts'

const mockAlerts = [
  {
    id: 'alert-1',
    name: 'Korean Valorant Prospects',
    markets: ['KR'],
    games: ['Valorant'],
    criteria: { minKDA: 2.5, minWinRate: 60 },
    notificationChannels: ['email', 'sms'],
    isActive: true,
    matchesFound: 12,
    lastTriggered: new Date().toISOString(),
    createdAt: new Date().toISOString()
  },
  {
    id: 'alert-2',
    name: 'Japanese Mobile Legends Players',
    markets: ['JP'],
    games: ['Mobile Legends'],
    criteria: { minWinRate: 55 },
    notificationChannels: ['email'],
    isActive: false,
    matchesFound: 8,
    createdAt: new Date().toISOString()
  }
]

jest.mock('@/lib/supabase/client', () => ({
  createClient: jest.fn(() => ({
    from: jest.fn((table) => {
      if (table === 'talent_ping_alerts') {
        return {
          select: jest.fn(() => ({
            eq: jest.fn(() => ({
              order: jest.fn().mockResolvedValue({
                data: mockAlerts
              })
            }))
          })),
          insert: jest.fn(() => ({
            select: jest.fn().mockResolvedValue({
              data: [{ ...mockAlerts[0], id: 'new-alert' }]
            })
          })),
          update: jest.fn(() => ({
            eq: jest.fn().mockResolvedValue({ error: null })
          })),
          delete: jest.fn(() => ({
            eq: jest.fn().mockResolvedValue({ error: null })
          }))
        }
      }
      return {}
    })
  }))
}))

describe('TalentPingAlerts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders alerts list correctly', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('Korean Valorant Prospects')).toBeInTheDocument()
      expect(screen.getByText('Japanese Mobile Legends Players')).toBeInTheDocument()
    })
  })

  it('displays alert statistics', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument() // Total alerts
      expect(screen.getByText('1')).toBeInTheDocument() // Active alerts
      expect(screen.getByText('20')).toBeInTheDocument() // Total matches (12 + 8)
    })
  })

  it('shows active and paused status correctly', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      const activeLabels = screen.getAllByText('ACTIVE')
      const pausedLabels = screen.getAllByText('PAUSED')
      
      expect(activeLabels).toHaveLength(1)
      expect(pausedLabels).toHaveLength(1)
    })
  })

  it('opens create alert modal', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    const createButton = screen.getByText(/Create New Alert/i)
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Create New Alert/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Korean Valorant Prospects/i)).toBeInTheDocument()
    })
  })

  it('validates alert form fields', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    // Open modal
    fireEvent.click(screen.getByText(/Create New Alert/i))
    
    await waitFor(() => {
      const createButton = screen.getAllByText(/Create Alert/i)[1] // Second one is in modal
      expect(createButton).toBeDisabled()
    })
  })

  it('creates new alert with valid data', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    // Open modal
    fireEvent.click(screen.getByText(/Create New Alert/i))
    
    await waitFor(() => {
      // Fill form
      const nameInput = screen.getByPlaceholderText(/Korean Valorant Prospects/i)
      fireEvent.change(nameInput, { target: { value: 'Test Alert' } })
      
      // Select market
      const koreaCheckbox = screen.getByLabelText(/South Korea/i)
      fireEvent.click(koreaCheckbox)
      
      // Select game
      const valorantCheckbox = screen.getByLabelText(/Valorant/i)
      fireEvent.click(valorantCheckbox)
      
      // Submit
      const createButton = screen.getAllByText(/Create Alert/i)[1]
      fireEvent.click(createButton)
    })
    
    await waitFor(() => {
      expect(screen.queryByText(/Create New Alert/i)).not.toBeInTheDocument()
    })
  })

  it('toggles alert active status', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      const pauseButtons = screen.getAllByText(/Pause/i)
      fireEvent.click(pauseButtons[0])
    })
    
    await waitFor(() => {
      expect(screen.getAllByText('PAUSED')).toHaveLength(2)
    })
  })

  it('deletes alert with confirmation', async () => {
    global.confirm = jest.fn(() => true)
    
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText(/Delete/i)
      fireEvent.click(deleteButtons[0])
    })
    
    expect(global.confirm).toHaveBeenCalled()
    
    await waitFor(() => {
      expect(screen.queryByText('Korean Valorant Prospects')).not.toBeInTheDocument()
    })
  })

  it('displays alert criteria correctly', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/KDA ≥ 2\.5/i)).toBeInTheDocument()
      expect(screen.getByText(/Win rate ≥ 60%/i)).toBeInTheDocument()
    })
  })

  it('shows notification channels', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('email')).toBeInTheDocument()
      expect(screen.getByText('sms')).toBeInTheDocument()
    })
  })

  it('displays matches found count', async () => {
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument()
    })
  })

  it('shows empty state when no alerts', async () => {
    jest.spyOn(require('@/lib/supabase/client'), 'createClient').mockReturnValue({
      from: jest.fn(() => ({
        select: jest.fn(() => ({
          eq: jest.fn(() => ({
            order: jest.fn().mockResolvedValue({ data: [] })
          }))
        }))
      }))
    })
    
    render(<TalentPingAlerts userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/No alerts yet/i)).toBeInTheDocument()
    })
  })
})
