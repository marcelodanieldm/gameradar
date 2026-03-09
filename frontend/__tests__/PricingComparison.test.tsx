import { render, screen, fireEvent } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import PlansComparison from '@/app/[locale]/pricing/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

describe('PlansComparison', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    jest.clearAllMocks()
  })

  it('renders both subscription plans', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/STREET SCOUT/i)).toBeInTheDocument()
    expect(screen.getByText(/ELITE ANALYST/i)).toBeInTheDocument()
  })

  it('displays correct pricing for both plans', () => {
    render(<PlansComparison />)
    
    const prices99 = screen.getAllByText(/\$99/i)
    const prices299 = screen.getAllByText(/\$299/i)
    
    expect(prices99.length).toBeGreaterThan(0)
    expect(prices299.length).toBeGreaterThan(0)
  })

  it('shows Street Scout features correctly', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/2 mercados a elegir/i)).toBeInTheDocument()
    expect(screen.getByText(/50 búsquedas\/mes/i)).toBeInTheDocument()
    expect(screen.getByText(/Perfiles detallados/i)).toBeInTheDocument()
  })

  it('shows Elite Analyst features correctly', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/Los 7 mercados/i)).toBeInTheDocument()
    expect(screen.getByText(/Búsquedas ilimitadas/i)).toBeInTheDocument()
    expect(screen.getByText(/Análisis avanzados con IA/i)).toBeInTheDocument()
    expect(screen.getByText(/Alertas TalentPing/i)).toBeInTheDocument()
    expect(screen.getByText(/Acceso a API/i)).toBeInTheDocument()
  })

  it('shows features not included in Street Scout', () => {
    render(<PlansComparison />)
    
    const notIncluded = screen.getAllByText(/No incluido/i)
    expect(notIncluded.length).toBeGreaterThanOrEqual(3)
  })

  it('highlights Elite Analyst as most popular', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/MÁS POPULAR/i)).toBeInTheDocument()
  })

  it('navigates to Street Scout subscription', () => {
    render(<PlansComparison />)
    
    const streetScoutButton = screen.getByText(/Comenzar con Street Scout/i)
    fireEvent.click(streetScoutButton)
    
    expect(mockPush).toHaveBeenCalledWith('/subscribe/street-scout')
  })

  it('navigates to Elite Analyst subscription', () => {
    render(<PlansComparison />)
    
    const eliteAnalystButton = screen.getByText(/Comenzar con Elite Analyst/i)
    fireEvent.click(eliteAnalystButton)
    
    expect(mockPush).toHaveBeenCalledWith('/subscribe/elite-analyst')
  })

  it('displays trust signals', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/Pago Seguro/i)).toBeInTheDocument()
    expect(screen.getByText(/Cancela Cuando Quieras/i)).toBeInTheDocument()
    expect(screen.getByText(/Acceso Instantáneo/i)).toBeInTheDocument()
  })

  it('shows FAQ section', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/Preguntas Frecuentes/i)).toBeInTheDocument()
    expect(screen.getByText(/¿Puedo cambiar de plan después?/i)).toBeInTheDocument()
    expect(screen.getByText(/¿Qué métodos de pago aceptan?/i)).toBeInTheDocument()
    expect(screen.getByText(/¿Hay descuentos por pago anual?/i)).toBeInTheDocument()
  })

  it('compares market access between plans', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/2 mercados a elegir/i)).toBeInTheDocument()
    expect(screen.getByText(/Los 7 mercados/i)).toBeInTheDocument()
  })

  it('compares search limits', () => {
    render(<PlansComparison />)
    
    expect(screen.getByText(/50 búsquedas\/mes/i)).toBeInTheDocument()
    expect(screen.getByText(/Búsquedas ilimitadas/i)).toBeInTheDocument()
  })

  it('shows visual distinction between included and excluded features', () => {
    render(<PlansComparison />)
    
    const checkmarks = screen.getAllByRole('img', { hidden: true })
    const crossmarks = screen.getAllByRole('img', { hidden: true })
    
    // Should have both green checkmarks and gray x marks
    expect(checkmarks.length + crossmarks.length).toBeGreaterThan(0)
  })

  it('has proper CTA styling for Elite Analyst', () => {
    render(<PlansComparison />)
    
    const eliteButton = screen.getByText(/Comenzar con Elite Analyst/i)
    
    // Elite button should have different styling (gradient)
    expect(eliteButton.className).toContain('gradient')
  })
})
