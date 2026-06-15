// Human-readable labels for raw sensor channel codes (presentation only).
// Mirror of backend/app/core/channels.py (CHANNEL_LABELS / CHANNEL_SHORT) -- keep in sync.
// Used wherever a raw channel code would otherwise be shown to a user; the raw
// code is kept as a value/secondary for traceability, never as the visible label.
export const CHANNEL_LABELS: Record<string, string> = {
  bpfi_amplitude_g: 'Inner-race bearing fault amplitude (BPFI)',
  vibration_peak_mm_s: 'Peak vibration (mm/s)',
  vibration_rms_mm_s: 'Overall vibration, RMS (mm/s)',
  bearing_temp_C: 'Bearing temperature (°C)',
  gmf_sideband_db: 'Gear-mesh sideband level (dB)',
  oil_fe_ppm: 'Iron particles in oil (ppm)',
  oil_temp_C: 'Oil temperature (°C)',
};

// Short label (lowercase, no unit) -- for inline driver clauses and the agent-reasoning
// trace, where the unit-bearing labels above (some contain a comma, e.g. "Overall
// vibration, RMS (mm/s)") would read as extra list items. Mirror of backend CHANNEL_SHORT.
export const CHANNEL_SHORT: Record<string, string> = {
  bpfi_amplitude_g: 'inner-race fault amplitude (BPFI)',
  vibration_peak_mm_s: 'peak vibration',
  vibration_rms_mm_s: 'overall vibration',
  bearing_temp_C: 'bearing temperature',
  gmf_sideband_db: 'gear-mesh sidebands',
  oil_fe_ppm: 'iron particles in oil',
  oil_temp_C: 'oil temperature',
};

export function channelLabel(code: string): string {
  return CHANNEL_LABELS[code] ?? code;
}

// Concise lowercase label for inline prose / the reasoning trace; falls back gracefully.
export function channelShort(code: string): string {
  return CHANNEL_SHORT[code] ?? CHANNEL_LABELS[code] ?? code;
}
