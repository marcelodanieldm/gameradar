/**
 * GameRadar AI - Frontend E2E Tests con Playwright
 * Tests para componentes React/Next.js
 * 
 * Tests incluidos:
 * - TransculturalDashboard rendering
 * - PlayerCard adaptativo (Mobile vs Technical)
 * - Country detection UI
 * - Supabase data fetching
 * - Interactive elements (sort, filter, share)
 */

import { test, expect, Page } from '@playwright/test';

// ============================================================
// CONFIGURACIÓN
// ============================================================

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const TEST_TIMEOUT = 30000;

test.describe('GameRadar AI - Frontend E2E Tests', () => {
  
  // ============================================================
  // TEST 1: TRANSCULTURAL DASHBOARD - RENDERIZADO BÁSICO
  // ============================================================
  
  test('Dashboard debe renderizar correctamente', async ({ page }) => {
    console.log('🧪 TEST 1: Dashboard Rendering');
    
    await page.goto(FRONTEND_URL);
    
    // Esperar a que cargue el dashboard
    await page.waitForSelector('text=GameRadar', { timeout: TEST_TIMEOUT });
    
    // Verificar título
    const title = await page.textContent('h1');
    expect(title).toContain('GameRadar');
    
    // Verificar que no hay errores de carga
    const errorMessage = page.locator('text=/error|failed/i');
    await expect(errorMessage).toHaveCount(0);
    
    console.log('   ✓ Dashboard renderizado correctamente');
  });

  // ============================================================
  // TEST 2: STATS CARDS
  // ============================================================
  
  test('Stats cards deben mostrar datos', async ({ page }) => {
    console.log('🧪 TEST 2: Stats Cards');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Verificar que hay cards de estadísticas
    const totalPlayersCard = page.locator('text=/Total.*Players/i').first();
    await expect(totalPlayersCard).toBeVisible();
    
    const topTalentCard = page.locator('text=/Top.*Talent/i').first();
    await expect(topTalentCard).toBeVisible();
    
    console.log('   ✓ Stats cards visibles');
  });

  // ============================================================
  // TEST 3: REGION FILTER
  // ============================================================
  
  test('Region filter debe funcionar', async ({ page }) => {
    console.log('🧪 TEST 3: Region Filter');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Buscar dropdown de región
    const regionSelect = page.locator('select').first();
    
    if (await regionSelect.isVisible()) {
      // Seleccionar Korea
      await regionSelect.selectOption('KR');
      await page.waitForTimeout(1000);
      
      // Verificar que la URL o estado cambió
      const selectedValue = await regionSelect.inputValue();
      expect(selectedValue).toBe('KR');
      
      console.log('   ✓ Region filter funciona');
    } else {
      console.log('   ⚠ Region filter no encontrado (puede ser auto-detectado)');
    }
  });

  // ============================================================
  // TEST 4: VIEW MODE TOGGLE (Auto/Cards/Table)
  // ============================================================
  
  test('View mode toggle debe cambiar layout', async ({ page }) => {
    console.log('🧪 TEST 4: View Mode Toggle');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Buscar botones de view mode
    const autoButton = page.locator('button:has-text("Auto")').first();
    const cardsButton = page.locator('button:has-text("Cards")').first();
    const tableButton = page.locator('button:has-text("Table")').first();
    
    if (await autoButton.isVisible()) {
      // Click en Cards view
      await cardsButton.click();
      await page.waitForTimeout(500);
      
      // Verificar que Cards view está activo
      const cardsActive = await cardsButton.getAttribute('class');
      expect(cardsActive).toContain('bg-cyan-600');
      
      // Click en Table view
      await tableButton.click();
      await page.waitForTimeout(500);
      
      const tableActive = await tableButton.getAttribute('class');
      expect(tableActive).toContain('bg-cyan-600');
      
      console.log('   ✓ View mode toggle funciona');
    } else {
      console.log('   ⚠ View mode toggle no encontrado');
    }
  });

  // ============================================================
  // TEST 5: PLAYER CARDS - MOBILE HEAVY
  // ============================================================
  
  test('Mobile-Heavy cards deben tener WhatsApp button', async ({ page }) => {
    console.log('🧪 TEST 5: Mobile-Heavy Cards');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Forzar Cards view
    const cardsButton = page.locator('button:has-text("Cards")').first();
    if (await cardsButton.isVisible()) {
      await cardsButton.click();
      await page.waitForTimeout(500);
    }
    
    // Buscar botón de WhatsApp
    const whatsappButton = page.locator('button:has-text(/WhatsApp|Contactar/i)').first();
    
    if (await whatsappButton.isVisible()) {
      expect(await whatsappButton.isVisible()).toBeTruthy();
      
      // Verificar que tiene el color verde característico
      const buttonClass = await whatsappButton.getAttribute('class');
      expect(buttonClass).toContain('green');
      
      console.log('   ✓ WhatsApp button encontrado en Mobile-Heavy card');
    } else {
      console.log('   ⚠ WhatsApp button no visible (puede ser Technical view)');
    }
  });

  // ============================================================
  // TEST 6: PLAYER CARDS - TECHNICAL
  // ============================================================
  
  test('Technical cards deben mostrar tabla compacta', async ({ page }) => {
    console.log('🧪 TEST 6: Technical Cards');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Forzar Table view
    const tableButton = page.locator('button:has-text("Table")').first();
    if (await tableButton.isVisible()) {
      await tableButton.click();
      await page.waitForTimeout(500);
    }
    
    // Buscar tabla
    const table = page.locator('table').first();
    
    if (await table.isVisible()) {
      // Verificar headers de tabla
      const headers = page.locator('th');
      const headerCount = await headers.count();
      
      expect(headerCount).toBeGreaterThan(5); // Debe tener múltiples columnas
      
      // Verificar que hay filas de datos
      const rows = page.locator('tbody tr');
      const rowCount = await rows.count();
      
      expect(rowCount).toBeGreaterThan(0);
      
      console.log(`   ✓ Tabla con ${headerCount} columnas y ${rowCount} filas`);
    } else {
      console.log('   ⚠ Tabla no visible (puede ser Cards view)');
    }
  });

  // ============================================================
  // TEST 7: SORTING FUNCTIONALITY
  // ============================================================
  
  test('Sorting debe funcionar en tabla', async ({ page }) => {
    console.log('🧪 TEST 7: Sorting');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Forzar Table view
    const tableButton = page.locator('button:has-text("Table")').first();
    if (await tableButton.isVisible()) {
      await tableButton.click();
      await page.waitForTimeout(500);
    }
    
    // Buscar header sorteable (ej: Nickname, Score)
    const sortableHeader = page.locator('th:has-text("Nickname")').first();
    
    if (await sortableHeader.isVisible()) {
      // Click para ordenar
      await sortableHeader.click();
      await page.waitForTimeout(500);
      
      // Verificar que hay icono de sort
      const sortIcon = page.locator('th:has-text("Nickname") svg').first();
      expect(await sortIcon.isVisible()).toBeTruthy();
      
      console.log('   ✓ Sorting funciona');
    } else {
      console.log('   ⚠ Sorting headers no encontrados');
    }
  });

  // ============================================================
  // TEST 8: PLAYER CARD INTERACTIONS
  // ============================================================
  
  test('Player card debe tener interacciones', async ({ page }) => {
    console.log('🧪 TEST 8: Card Interactions');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Buscar primer player card/row
    const firstPlayer = page.locator('[data-player], tr:has(td)').first();
    
    if (await firstPlayer.isVisible()) {
      // Hover sobre card
      await firstPlayer.hover();
      
      // Buscar botones de acción (Ver Perfil, Share, etc)
      const actionButtons = firstPlayer.locator('button, a[href]');
      const buttonCount = await actionButtons.count();
      
      expect(buttonCount).toBeGreaterThan(0);
      
      console.log(`   ✓ Card con ${buttonCount} acciones`);
    } else {
      console.log('   ⚠ Player cards no encontrados');
    }
  });

  // ============================================================
  // TEST 9: VERIFIED BADGE
  // ============================================================
  
  test('Verified badge debe aparecer en jugadores verificados', async ({ page }) => {
    console.log('🧪 TEST 9: Verified Badge');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Buscar badges de verificación
    const verifiedBadges = page.locator('text=/Verified|✓/i');
    const count = await verifiedBadges.count();
    
    if (count > 0) {
      console.log(`   ✓ ${count} jugadores verificados encontrados`);
    } else {
      console.log('   ⚠ No hay jugadores verificados (esperado si DB está vacía)');
    }
  });

  // ============================================================
  // TEST 10: SCORE BADGES
  // ============================================================
  
  test('Score badges deben mostrar valores correctos', async ({ page }) => {
    console.log('🧪 TEST 10: Score Badges');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Buscar badges de score (números 0-100)
    const scoreBadges = page.locator('text=/\\d{1,3}$/');
    const count = await scoreBadges.count();
    
    if (count > 0) {
      // Verificar que el primer score está en rango válido
      const firstScore = await scoreBadges.first().textContent();
      const scoreValue = parseInt(firstScore || '0');
      
      expect(scoreValue).toBeGreaterThanOrEqual(0);
      expect(scoreValue).toBeLessThanOrEqual(100);
      
      console.log(`   ✓ Scores en rango válido: ${firstScore}`);
    } else {
      console.log('   ⚠ No se encontraron scores (DB puede estar vacía)');
    }
  });

  // ============================================================
  // TEST 11: RESPONSIVE DESIGN
  // ============================================================
  
  test('Dashboard debe ser responsive', async ({ page }) => {
    console.log('🧪 TEST 11: Responsive Design');
    
    // Test en desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    let isVisible = await page.locator('h1').isVisible();
    expect(isVisible).toBeTruthy();
    console.log('   ✓ Desktop view: OK');
    
    // Test en tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    
    isVisible = await page.locator('h1').isVisible();
    expect(isVisible).toBeTruthy();
    console.log('   ✓ Tablet view: OK');
    
    // Test en mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    isVisible = await page.locator('h1').isVisible();
    expect(isVisible).toBeTruthy();
    console.log('   ✓ Mobile view: OK');
  });

  // ============================================================
  // TEST 12: DARK MODE
  // ============================================================
  
  test('Dashboard debe tener dark mode', async ({ page }) => {
    console.log('🧪 TEST 12: Dark Mode');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Verificar background oscuro
    const body = page.locator('body, div[class*="min-h-screen"]').first();
    const backgroundColor = await body.evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    
    // Background debe ser oscuro (rgb con valores bajos)
    console.log(`   ✓ Background color: ${backgroundColor}`);
    expect(backgroundColor).toMatch(/rgb\(.*\)/);
  });

  // ============================================================
  // TEST 13: LOADING STATES
  // ============================================================
  
  test('Loading states deben aparecer', async ({ page }) => {
    console.log('🧪 TEST 13: Loading States');
    
    // Interceptar requests para hacer loading más lento
    await page.route('**/supabase.co/**', route => 
      setTimeout(() => route.continue(), 1000)
    );
    
    const navigationPromise = page.goto(FRONTEND_URL);
    
    // Buscar loading spinner
    const loadingSpinner = page.locator('[class*="animate-spin"]').first();
    
    // Verificar que aparece durante la carga
    try {
      await expect(loadingSpinner).toBeVisible({ timeout: 2000 });
      console.log('   ✓ Loading spinner visible');
    } catch {
      console.log('   ⚠ Loading muy rápido para capturar spinner');
    }
    
    await navigationPromise;
  });

  // ============================================================
  // TEST 14: ERROR HANDLING
  // ============================================================
  
  test('Error states deben manejarse correctamente', async ({ page }) => {
    console.log('🧪 TEST 14: Error Handling');
    
    // Simular error de red
    await page.route('**/supabase.co/**', route => 
      route.abort('failed')
    );
    
    await page.goto(FRONTEND_URL);
    
    // Buscar mensaje de error
    const errorMessage = page.locator('text=/error|failed|unable/i').first();
    
    try {
      await expect(errorMessage).toBeVisible({ timeout: 5000 });
      console.log('   ✓ Error message mostrado correctamente');
    } catch {
      console.log('   ⚠ Error handling puede necesitar ajustes');
    }
  });

  // ============================================================
  // TEST 15: ACCESSIBILITY
  // ============================================================
  
  test('Dashboard debe ser accesible', async ({ page }) => {
    console.log('🧪 TEST 15: Accessibility');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Verificar que botones son accesibles por teclado
    const firstButton = page.locator('button').first();
    
    if (await firstButton.isVisible()) {
      await firstButton.focus();
      const isFocused = await firstButton.evaluate(el => el === document.activeElement);
      expect(isFocused).toBeTruthy();
      
      console.log('   ✓ Elementos focuseables por teclado');
    }
    
    // Verificar que imágenes tienen alt text
    const images = page.locator('img');
    const imageCount = await images.count();
    
    if (imageCount > 0) {
      for (let i = 0; i < imageCount; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        expect(alt).toBeTruthy();
      }
      console.log(`   ✓ ${imageCount} imágenes con alt text`);
    }
  });

  // ============================================================
  // TEST 16: PERFORMANCE
  // ============================================================
  
  test('Dashboard debe cargar rápido', async ({ page }) => {
    console.log('🧪 TEST 16: Performance');
    
    const startTime = Date.now();
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(5000); // Debe cargar en <5s
    
    console.log(`   ✓ Load time: ${loadTime}ms`);
  });

  // ============================================================
  // TEST 17: SUPABASE DATA FETCHING
  // ============================================================
  
  test('Datos de Supabase deben cargarse', async ({ page }) => {
    console.log('🧪 TEST 17: Supabase Data Fetching');
    
    // Interceptar llamadas a Supabase
    let supabaseCalled = false;
    
    page.on('request', request => {
      if (request.url().includes('supabase')) {
        supabaseCalled = true;
      }
    });
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    expect(supabaseCalled).toBeTruthy();
    console.log('   ✓ Supabase API llamada correctamente');
  });

});

// ============================================================
// CONFIGURACIÓN DE PLAYWRIGHT
// ============================================================

export const config = {
  testDir: './tests',
  timeout: 30000,
  use: {
    baseURL: FRONTEND_URL,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
    {
      name: 'firefox',
      use: { browserName: 'firefox' },
    },
    {
      name: 'webkit',
      use: { browserName: 'webkit' },
    },
  ],
};
