// Elite Salon Admin — Design System & Config
// "The Digital Concierge" — High-End Salon Management

import { Platform } from 'react-native';

// Point to your live Render backend
const API_BASE = 'https://ai-saloon-calling-agent.onrender.com';

export const API_URL = API_BASE + '/api/admin';

// Elite Salon Custom Theme extracted from Stitch
export const COLORS = {
  // Core
  bg: '#131313',
  surface: '#131313',
  surfaceBright: '#393939',
  surfaceContainerLow: '#1c1b1b',
  surfaceContainer: '#20201f',
  surfaceContainerHigh: '#2a2a2a',
  surfaceContainerHighest: '#353535',

  // Primary
  primary: '#f2ca50',
  primaryContainer: '#d4af37',
  onPrimary: '#3c2f00',
  onPrimaryContainer: '#554300',

  // Secondary
  secondary: '#dac58d',
  secondaryContainer: '#544519',

  // Tertiary
  tertiary: '#bfcdff',
  tertiaryContainer: '#97b0ff',

  // Text / Outline
  onSurface: '#e5e2e1',
  onSurfaceVariant: '#d0c5af',
  outline: '#99907c',
  outlineVariant: '#4d4635',

  // Semantic
  error: '#ffb4ab',
  errorContainer: '#93000a',
  success: '#4ade80',

  // Navigation
  navBg: 'rgba(19, 19, 19, 0.92)',
  navActive: '#f2ca50',
  navInactive: '#99907c',
};

// Layout radii according to tonal layer elevation
export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

// Fallback stacks to match Noto Serif and Inter without heavy library bindings
export const FONTS = {
  display: Platform.OS === 'ios' ? 'Georgia' : 'serif',
  body: Platform.OS === 'ios' ? 'System' : 'sans-serif',
};
