import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import APIAccessPanel from '@/components/APIAccessPanel'

const mockApiKeys = [
  {
    id: 'key-1',
    name: 'Production Server',
    key: 'gr_live_abcdefgh123456789012345678901234',
    createdAt: new Date('2026-01-01').toISOString(),
    lastUsed: new Date('2026-03-08').toISOString(),
    requestsToday: 523,
    isActive: true
  },
  {
    id: 'key-2',
    name: 'Development Environment',
    key: 'gr_live_xyz98765432109876543210987654321',
    createdAt: new Date('2026-02-01').toISOString(),
    requestsToday: 42,
    isActive: false
  }
]

jest.mock('@/lib/supabase/client', () => ({
  createClient: jest.fn(() => ({
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          order: jest.fn().mockResolvedValue({
            data: mockApiKeys
          })
        }))
      })),
      insert: jest.fn(() => ({
        select: jest.fn().mockResolvedValue({
          data: [{
            id: 'new-key',
            name: 'Test Key',
            key: 'gr_live_newkey123456789012345678901234',
            createdAt: new Date().toISOString(),
            requestsToday: 0,
            isActive: true
          }]
        })
      })),
      update: jest.fn(() => ({
        eq: jest.fn().mockResolvedValue({ error: null })
      })),
      delete: jest.fn(() => ({
        eq: jest.fn().mockResolvedValue({ error: null })
      }))
    }))
  }))
}))

describe('APIAccessPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined)
      }
    })
  })

  it('renders API access panel correctly', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/API Access/i)).toBeInTheDocument()
    })
  })

  it('displays API keys statistics', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument() // Total keys
      expect(screen.getByText('1')).toBeInTheDocument() // Active keys
      expect(screen.getByText('565')).toBeInTheDocument() // Total requests (523 + 42)
    })
  })

  it('lists all API keys', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('Production Server')).toBeInTheDocument()
      expect(screen.getByText('Development Environment')).toBeInTheDocument()
    })
  })

  it('masks API keys for security', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      const maskedKeys = screen.getAllByText(/gr_live_\w{8}•+/i)
      expect(maskedKeys.length).toBeGreaterThan(0)
    })
  })

  it('copies API key to clipboard', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      const copyButtons = screen.getAllByText(/Copy/i)
      fireEvent.click(copyButtons[0])
    })
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'gr_live_abcdefgh123456789012345678901234'
    )
    
    await waitFor(() => {
      expect(screen.getByText(/Copied!/i)).toBeInTheDocument()
    })
  })

  it('opens create API key modal', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    const createButton = screen.getByText(/Create API Key/i)
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Production Server/i)).toBeInTheDocument()
    })
  })

  it('creates new API key', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    fireEvent.click(screen.getByText(/Create API Key/i))
    
    await waitFor(() => {
      const nameInput = screen.getByPlaceholderText(/Production Server/i)
      fireEvent.change(nameInput, { target: { value: 'Test Key' } })
      
      const createButton = screen.getAllByText(/Create Key/i)[0]
      fireEvent.click(createButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Test Key')).toBeInTheDocument()
    })
  })

  it('toggles API key active status', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      const toggleButtons = screen.getAllByRole('button', { name: /⏸️|▶️/i })
      fireEvent.click(toggleButtons[0])
    })
    
    await waitFor(() => {
      const disabledLabels = screen.getAllByText('DISABLED')
      expect(disabledLabels.length).toBeGreaterThan(0)
    })
  })

  it('deletes API key with confirmation', async () => {
    global.confirm = jest.fn(() => true)
    
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText(/🗑️/i)
      fireEvent.click(deleteButtons[0])
    })
    
    expect(global.confirm).toHaveBeenCalledWith(
      expect.stringContaining('Are you sure')
    )
  })

  it('displays API documentation', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/API Documentation/i)).toBeInTheDocument()
      expect(screen.getByText(/Authentication/i)).toBeInTheDocument()
      expect(screen.getByText(/Search Players/i)).toBeInTheDocument()
      expect(screen.getByText(/Rate Limits/i)).toBeInTheDocument()
    })
  })

  it('shows curl example', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/curl -X GET/i)).toBeInTheDocument()
      expect(screen.getByText(/Authorization: Bearer YOUR_API_KEY/i)).toBeInTheDocument()
    })
  })

  it('displays response codes', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('200 OK')).toBeInTheDocument()
      expect(screen.getByText('401 Unauthorized')).toBeInTheDocument()
      expect(screen.getByText('429 Too Many Requests')).toBeInTheDocument()
      expect(screen.getByText('500 Server Error')).toBeInTheDocument()
    })
  })

  it('shows SDK options', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument()
      expect(screen.getByText('Node.js')).toBeInTheDocument()
      expect(screen.getByText('Java')).toBeInTheDocument()
    })
  })

  it('displays last used timestamp', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/Last used:/i)).toBeInTheDocument()
    })
  })

  it('shows requests count per key', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/Requests today: 523/i)).toBeInTheDocument()
      expect(screen.getByText(/Requests today: 42/i)).toBeInTheDocument()
    })
  })

  it('displays empty state when no keys', async () => {
    jest.spyOn(require('@/lib/supabase/client'), 'createClient').mockReturnValue({
      from: jest.fn(() => ({
        select: jest.fn(() => ({
          eq: jest.fn(() => ({
            order: jest.fn().mockResolvedValue({ data: [] })
          }))
        }))
      }))
    })
    
    render(<APIAccessPanel userId="test-user-id" />)
    
    await waitFor(() => {
      expect(screen.getByText(/No API keys yet/i)).toBeInTheDocument()
    })
  })

  it('validates key name before creation', async () => {
    render(<APIAccessPanel userId="test-user-id" />)
    
    fireEvent.click(screen.getByText(/Create API Key/i))
    
    await waitFor(() => {
      const createButton = screen.getAllByText(/Create Key/i)[0]
      expect(createButton).toBeDisabled()
    })
  })
})
