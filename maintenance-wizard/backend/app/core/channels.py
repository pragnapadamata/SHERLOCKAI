"""Human-readable labels for raw sensor channel codes (presentation only).

Single source of truth for turning channel codes (``bpfi_amplitude_g`` etc.) into
text shown to a user. Mirrored on the frontend in ``src/lib/channels.ts`` -- keep
the two in sync. This module never touches detection/scoring; it only renames.
"""

from __future__ import annotations

# Primary human label (with unit) -- used wherever a single channel is shown to a
# user (sensor dropdowns, chart series, provenance drivers).
CHANNEL_LABELS: dict[str, str] = {
    "bpfi_amplitude_g": "Inner-race bearing fault amplitude (BPFI)",
    "vibration_peak_mm_s": "Peak vibration (mm/s)",
    "vibration_rms_mm_s": "Overall vibration, RMS (mm/s)",
    "bearing_temp_C": "Bearing temperature (°C)",
    "gmf_sideband_db": "Gear-mesh sideband level (dB)",
    "oil_fe_ppm": "Iron particles in oil (ppm)",
    "oil_temp_C": "Oil temperature (°C)",
}

# Short label (lowercase, no unit) -- for inline driver clauses in prose headlines.
CHANNEL_SHORT: dict[str, str] = {
    "bpfi_amplitude_g": "inner-race fault amplitude (BPFI)",
    "vibration_peak_mm_s": "peak vibration",
    "vibration_rms_mm_s": "overall vibration",
    "bearing_temp_C": "bearing temperature",
    "gmf_sideband_db": "gear-mesh sidebands",
    "oil_fe_ppm": "iron particles in oil",
    "oil_temp_C": "oil temperature",
}

# Coarse measurement family -- drives natural-language trend phrasing.
CHANNEL_FAMILY: dict[str, str] = {
    "bpfi_amplitude_g": "vibration",
    "vibration_peak_mm_s": "vibration",
    "vibration_rms_mm_s": "vibration",
    "gmf_sideband_db": "vibration",
    "bearing_temp_C": "temperature",
    "oil_temp_C": "temperature",
    "oil_fe_ppm": "oil",
}


def channel_label(code: str) -> str:
    """Full human label for a channel code; falls back to the raw code."""

    return CHANNEL_LABELS.get(code, code)


def channel_short(code: str) -> str:
    """Concise lowercase label for inline prose; falls back gracefully."""

    return CHANNEL_SHORT.get(code, CHANNEL_LABELS.get(code, code))


def humanize_drivers(codes: list[str]) -> str:
    """Render a list of driver channels as readable prose, never raw codes.

    Channels that share the "... vibration" tail are merged into a single phrase
    ("peak & overall vibration") so the line reads naturally. Returns "" for an
    empty list.
    """

    out: list[str | None] = []
    vib: list[str] = []
    vib_placed = False
    for code in codes:
        if not code:
            continue
        short = channel_short(code)
        if short.endswith(" vibration"):
            vib.append(short[: -len(" vibration")])
            if not vib_placed:
                out.append(None)  # placeholder for the merged vibration phrase
                vib_placed = True
        else:
            out.append(short)
    if vib:
        phrase = " & ".join(vib) + " vibration"
        out = [phrase if item is None else item for item in out]
    return ", ".join(item for item in out if item)
