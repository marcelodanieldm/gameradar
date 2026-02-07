'use client';

import { useCountryDetection } from './useCountryDetection';

export type RegionType = 'mobile-heavy' | 'analytical' | 'default';

export interface RegionConfig {
  type: RegionType;
  countryCode: string;
  gridCols: string;
  cardSize: 'large' | 'compact';
  typography: 'sans-serif' | 'serif';
  neonEffects: boolean;
  tableView: boolean;
}

const MOBILE_HEAVY_COUNTRIES = ['IN', 'VN', 'ID', 'PH', 'TH'];
const ANALYTICAL_COUNTRIES = ['KR', 'CN', 'JP', 'TW'];

/**
 * Hook for detecting user region and returning optimized UI configuration
 * 
 * @returns RegionConfig - Configuration object with region-specific settings
 * 
 * @example
 * ```tsx
 * const region = useRegion();
 * 
 * // Mobile-Heavy (India/Vietnam)
 * // { type: 'mobile-heavy', gridCols: 'grid-cols-1', neonEffects: true }
 * 
 * // Analytical (Korea/China/Japan)
 * // { type: 'analytical', gridCols: 'grid-cols-3', tableView: true }
 * ```
 */
export function useRegion(): RegionConfig {
  const countryCode = useCountryDetection();

  // Mobile-Heavy Region: India, Vietnam, Indonesia, Philippines, Thailand
  if (MOBILE_HEAVY_COUNTRIES.includes(countryCode)) {
    return {
      type: 'mobile-heavy',
      countryCode,
      gridCols: 'grid-cols-1',
      cardSize: 'large',
      typography: 'sans-serif',
      neonEffects: true,
      tableView: false,
    };
  }

  // Analytical Region: Korea, China, Japan, Taiwan
  if (ANALYTICAL_COUNTRIES.includes(countryCode)) {
    return {
      type: 'analytical',
      countryCode,
      gridCols: 'grid-cols-3',
      cardSize: 'compact',
      typography: 'serif',
      neonEffects: false,
      tableView: true,
    };
  }

  // Default fallback
  return {
    type: 'default',
    countryCode,
    gridCols: 'grid-cols-2',
    cardSize: 'large',
    typography: 'sans-serif',
    neonEffects: false,
    tableView: false,
  };
}

/**
 * Helper function to check if current region is mobile-heavy
 */
export function isMobileHeavyRegion(countryCode: string): boolean {
  return MOBILE_HEAVY_COUNTRIES.includes(countryCode);
}

/**
 * Helper function to check if current region is analytical
 */
export function isAnalyticalRegion(countryCode: string): boolean {
  return ANALYTICAL_COUNTRIES.includes(countryCode);
}
