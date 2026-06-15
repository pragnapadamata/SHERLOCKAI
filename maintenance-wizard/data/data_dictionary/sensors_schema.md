> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Sensor time-series (`data/raw/sensors/*.parquet`)

**Source class.** programmatic (generate_sensors.py)

**Sampling.** 10-minute aggregated features (144 samples/day).

**Window.** 16 weeks ending at the simulation anchor 2026-06-06T06:00:00 (first sample 2026-02-14T06:10:00).

**Common columns.** `timestamp_utc` (datetime), `equipment_id` (str), the asset-specific channels below, `regime` (baseline|degrading|alert|action), `anomaly_flag` (bool), `note` (str).

## ISO 10816-3 velocity RMS zones (mm/s)

- baseline / good: RMS <= 1.4
- alert (zone B/C): 1.4 < RMS <= 2.8
- action (zone C/D): 2.8 < RMS <= 4.5
- damage onset: RMS > 4.5

`regime` is derived from the primary RMS channel against these boundaries; `degrading` marks samples in the degradation window that are still below the alert zone. `anomaly_flag` is true for scripted anomalies and for any sample in the alert or action zone.

## HSM-F3-GBX - F3 main drive gearbox (herringbone / planetary)

Baseline 8 weeks, degradation 8 weeks. Scripted anomalies: none scripted.

| Channel | Unit | Baseline | Degrades to | Description |
| --- | --- | --- | --- | --- |
| `vibration_rms_mm_s` | mm/s | 1.2 | 2.5 mm/s | Overall velocity RMS (ISO 10816-3). |
| `gmf_sideband_db` | dB | -32.0 | -20.0 dB | Gear-mesh-frequency sideband amplitude. |
| `oil_fe_ppm` | ppm | 18.0 | 34.0 ppm | Oil iron-particle concentration. |
| `oil_temp_C` | degC | 52.0 | 55.0 degC | Gearbox oil temperature. |
| `motor_current_A` | A | 600.0 | 615.0 A | Drive motor current. |

## HSM-F2-WRB - F2 finishing stand work-roll bearing (drive side)

Baseline 10 weeks, degradation 6 weeks. Scripted anomalies: day 108: Sudden vibration step change - suspected inner-race defect..

| Channel | Unit | Baseline | Degrades to | Description |
| --- | --- | --- | --- | --- |
| `vibration_rms_mm_s` | mm/s | 1.0 | 2.0 mm/s | Overall velocity RMS (ISO 10816-3). |
| `vibration_peak_mm_s` | mm/s | 1.6 | 3.2 mm/s | Peak velocity. |
| `bpfi_amplitude_g` | g | 0.05 | 0.45 g | Ball-pass inner-race defect-frequency amplitude. |
| `bearing_temp_C` | degC | 45.0 | 53.0 degC | Bearing housing temperature. |
| `motor_current_A` | A | 480.0 | 490.0 A | Stand drive current. |

## HSM-DC-MND - Down-coiler mandrel and wrapper-roll assembly

Baseline 16 weeks, degradation 0 weeks. Scripted anomalies: day 30: Wrapper-roll vibration tick.; day 75: Wrapper-roll vibration tick.; day 100: Wrapper-roll vibration tick..

| Channel | Unit | Baseline | Degrades to | Description |
| --- | --- | --- | --- | --- |
| `vibration_rms_mm_s` | mm/s | 1.1 | flat | Overall velocity RMS (ISO 10816-3). |
| `bearing_temp_C` | degC | 40.0 | flat | Wrapper-roll bearing temperature. |
| `hydraulic_pressure_bar` | bar | 180.0 | flat | Mandrel hydraulic pressure. |
| `motor_current_A` | A | 350.0 | flat | Coiler drive current. |
| `coil_tension_kN` | kN | 120.0 | flat | Strip coiling tension. |
