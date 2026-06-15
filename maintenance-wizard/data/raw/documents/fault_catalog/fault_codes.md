> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Fault / Error Code Catalog

## Overview

This catalog lists every fault/error code in the prototype, with its meaning, likely cause, recommended action, and cross-links to the relevant equipment, standard operating procedures, and spare parts. It mirrors `data/raw/structured/fault_catalog.csv`.

## Catalog

### [[FAULT:F3-GBX-002]] - Rising gear-mesh sidebands with oil iron-particle trend

- Equipment: [[ASSET:HSM-F3-GBX]]
- Severity: critical
- Meaning: Gear-mesh-frequency sidebands and oil Fe particle count rising together over weeks.
- Likely cause: Stage-2 gear-tooth pitting progressing toward tooth fracture.
- Recommended action: Confirm by vibration spectrum and oil analysis; plan Stage-2 gear set replacement before fracture.
- Related SOPs: [[SOP:SOP-GBX-001]], [[SOP:SOP-OIL-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:GBX-GEAR-SET-01]]

### [[FAULT:F3-GBX-001]] - Gearbox oil over-temperature

- Equipment: [[ASSET:HSM-F3-GBX]]
- Severity: medium
- Meaning: Oil temperature exceeds normal operating band.
- Likely cause: Cooler fouling, low oil level, or excessive load.
- Recommended action: Check cooler and oil level; sample oil per SOP-OIL-001.
- Related SOPs: [[SOP:SOP-OIL-001]]
- Related spares: [[PART:GBX-OIL-FILT-01]]

### [[FAULT:F3-GBX-003]] - Gearbox low oil level

- Equipment: [[ASSET:HSM-F3-GBX]]
- Severity: high
- Meaning: Lubricant level below minimum sight-glass mark.
- Likely cause: Leak at seal or drain; top-up overdue.
- Recommended action: Inspect seals, top up, and re-sample oil.
- Related SOPs: [[SOP:SOP-OIL-001]]
- Related spares: [[PART:GBX-OIL-FILT-01]]

### [[FAULT:F3-GBX-004]] - Gearbox broadband vibration high

- Equipment: [[ASSET:HSM-F3-GBX]]
- Severity: critical
- Meaning: Overall vibration RMS in ISO action zone.
- Likely cause: Advanced gear or bearing damage, or misalignment.
- Recommended action: Stop at next opportunity; inspect per SOP-GBX-001.
- Related SOPs: [[SOP:SOP-GBX-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:GBX-GEAR-SET-01]], [[PART:GBX-BRG-SET-01]]

### [[FAULT:F2-WRB-001]] - Bearing temperature and vibration rising with inner-race signature

- Equipment: [[ASSET:HSM-F2-WRB]]
- Severity: high
- Meaning: Bearing temperature and vibration RMS rising together with a ball-pass inner-race (BPFI) signature.
- Likely cause: Lubrication starvation leading to inner-race spalling.
- Recommended action: Perform immediate lubrication check per SOP-LUB-001; plan bearing replacement per SOP-BRG-001.
- Related SOPs: [[SOP:SOP-LUB-001]], [[SOP:SOP-BRG-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:BRG-F2-TRB-01]], [[PART:GREASE-EP2-DRUM]]

### [[FAULT:F2-WRB-002]] - Bearing over-temperature trip

- Equipment: [[ASSET:HSM-F2-WRB]]
- Severity: critical
- Meaning: Bearing temperature crosses the protective trip threshold.
- Likely cause: Loss of lubrication or advanced spalling.
- Recommended action: Stop the stand; do not restart before lubrication and inspection.
- Related SOPs: [[SOP:SOP-LUB-001]], [[SOP:SOP-BRG-001]]
- Related spares: [[PART:BRG-F2-TRB-01]]

### [[FAULT:F2-WRB-003]] - Bearing housing looseness

- Equipment: [[ASSET:HSM-F2-WRB]]
- Severity: medium
- Meaning: Sub-harmonic and harmonic vibration pattern suggesting mechanical looseness.
- Likely cause: Loose housing bolts or worn fit.
- Recommended action: Torque-check housing; inspect fits per SOP-BRG-001.
- Related SOPs: [[SOP:SOP-BRG-001]]
- Related spares: [[PART:BRG-F2-TRB-01]]

### [[FAULT:DC-MND-001]] - Mandrel segment wear

- Equipment: [[ASSET:HSM-DC-MND]]
- Severity: high
- Meaning: Mandrel segment clearance beyond tolerance.
- Likely cause: Abrasive wear of segment faces over service life.
- Recommended action: Measure segment clearance per SOP-MND-001; replace segment set if out of tolerance.
- Related SOPs: [[SOP:SOP-MND-001]]
- Related spares: [[PART:DC-MND-SEG-01]]

### [[FAULT:DC-MND-002]] - Wrapper-roll bearing vibration

- Equipment: [[ASSET:HSM-DC-MND]]
- Severity: medium
- Meaning: Intermittent wrapper-roll bearing vibration ticks.
- Likely cause: Early wrapper-roll bearing degradation.
- Recommended action: Trend vibration; replace wrapper-roll bearing at next planned stop.
- Related SOPs: [[SOP:SOP-BRG-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:DC-WRAP-BRG-01]]

### [[FAULT:DC-PROC-001]] - Alpha surface-defect cluster on coiled product

- Equipment: [[ASSET:HSM-DC-MND]]
- Severity: medium
- Meaning: Cluster of Alpha surface defects on finished coils correlated with upstream multi-stage process parameters.
- Likely cause: Process-parameter excursions interacting with equipment condition (assessed by the Phase 3 defect model).
- Recommended action: Review process parameters for flagged coils; cross-check mandrel and wrapper-roll condition.
- Related SOPs: [[SOP:SOP-MND-001]]
- Related spares: [[PART:DC-WRAP-BRG-01]]

### [[FAULT:DSC-PMP-001]] - Low descaling pressure

- Equipment: [[ASSET:HSM-DSC-PMP]]
- Severity: medium
- Meaning: Header pressure below descaling setpoint.
- Likely cause: Plunger-seal wear or valve leakage.
- Recommended action: Replace seal kit; inspect plunger.
- Related SOPs: [[SOP:SOP-BRG-001]]
- Related spares: [[PART:DSC-PMP-SEAL-01]], [[PART:DSC-PMP-PLUNGER-01]]

### [[FAULT:RM-MOT-001]] - Stator winding over-temperature

- Equipment: [[ASSET:HSM-RM-MOT]]
- Severity: high
- Meaning: Winding RTD temperature trending high.
- Likely cause: Insulation degradation or cooling loss.
- Recommended action: Reduce load; plan insulation test and rewind.
- Related SOPs: [[SOP:SOP-VIB-001]]
- Related spares: [[PART:RM-MOT-WIND-01]]

### [[FAULT:RM-MOT-002]] - Motor drive-end bearing vibration

- Equipment: [[ASSET:HSM-RM-MOT]]
- Severity: medium
- Meaning: Drive-end bearing vibration rising.
- Likely cause: Bearing wear.
- Recommended action: Trend and replace drive-end bearing.
- Related SOPs: [[SOP:SOP-BRG-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:RM-MOT-BRG-01]]

### [[FAULT:ROT-PMP-001]] - Cooling pump cavitation

- Equipment: [[ASSET:HSM-ROT-PMP]]
- Severity: medium
- Meaning: Pump cavitation signature with flow fluctuation.
- Likely cause: Suction restriction or low NPSH.
- Recommended action: Check suction strainer; inspect impeller.
- Related SOPs: [[SOP:SOP-VIB-001]]
- Related spares: [[PART:ROT-PMP-IMP-01]]

### [[FAULT:AGC-HYD-001]] - Servo-valve contamination causing gauge variation

- Equipment: [[ASSET:HSM-AGC-HYD]]
- Severity: high
- Meaning: Strip-gauge variation correlated with sluggish servo-valve response.
- Likely cause: Hydraulic fluid contamination.
- Recommended action: Flush system; replace servo valve if response is out of spec.
- Related SOPs: [[SOP:SOP-OIL-001]]
- Related spares: [[PART:AGC-SERVO-VALVE-01]]

### [[FAULT:AGC-HYD-002]] - Low hydraulic pressure

- Equipment: [[ASSET:HSM-AGC-HYD]]
- Severity: medium
- Meaning: AGC supply pressure below setpoint.
- Likely cause: Pump wear or internal leakage.
- Recommended action: Check pump and seals; replace seal kit.
- Related SOPs: [[SOP:SOP-OIL-001]]
- Related spares: [[PART:AGC-SEAL-KIT-01]]

### [[FAULT:F1-WRB-001]] - F1 bearing vibration rising

- Equipment: [[ASSET:HSM-F1-WRB]]
- Severity: medium
- Meaning: F1 work-roll bearing vibration trending up.
- Likely cause: Lubrication or early spalling, as seen on the F-stand family.
- Recommended action: Lubricate per SOP-LUB-001; trend and plan replacement.
- Related SOPs: [[SOP:SOP-LUB-001]], [[SOP:SOP-BRG-001]]
- Related spares: [[PART:BRG-F1-TRB-01]]

### [[FAULT:LUB-UNIT-001]] - Lubrication filter clogging / low downstream flow

- Equipment: [[ASSET:HSM-LUB-UNIT]]
- Severity: high
- Meaning: Downstream lubrication flow falling with rising filter differential pressure.
- Likely cause: Filter element clogged.
- Recommended action: Replace filter element per SOP-LUB-001.
- Related SOPs: [[SOP:SOP-LUB-001]]
- Related spares: [[PART:LUB-FILT-01]]

### [[FAULT:LUB-UNIT-002]] - Lubrication reservoir low level

- Equipment: [[ASSET:HSM-LUB-UNIT]]
- Severity: medium
- Meaning: Grease/oil reservoir below minimum.
- Likely cause: Consumption without refill or a leak.
- Recommended action: Refill and inspect for leaks.
- Related SOPs: [[SOP:SOP-LUB-001]]
- Related spares: [[PART:GREASE-EP2-DRUM]]

### [[FAULT:F4F7-BRG-001]] - F4-F7 bearing vibration (group)

- Equipment: [[ASSET:HSM-F4-F7-BRG]]
- Severity: medium
- Meaning: One of the F4-F7 stand bearings shows rising vibration.
- Likely cause: Lubrication or wear on a finishing-stand bearing.
- Recommended action: Identify the stand; lubricate and trend.
- Related SOPs: [[SOP:SOP-LUB-001]], [[SOP:SOP-VIB-001]]
- Related spares: [[PART:BRG-F4F7-TRB-01]]

### [[FAULT:DSC-PMP-002]] - Descaler pump vibration

- Equipment: [[ASSET:HSM-DSC-PMP]]
- Severity: low
- Meaning: Pump vibration rising.
- Likely cause: Bearing or coupling wear.
- Recommended action: Inspect coupling and bearings.
- Related SOPs: [[SOP:SOP-VIB-001]]
- Related spares: [[PART:DSC-PMP-PLUNGER-01]]

### [[FAULT:ROT-PMP-002]] - Cooling pump seal leak

- Equipment: [[ASSET:HSM-ROT-PMP]]
- Severity: low
- Meaning: Visible leak at pump mechanical seal.
- Likely cause: Seal wear.
- Recommended action: Replace mechanical seal.
- Related SOPs: [[SOP:SOP-BRG-001]]
- Related spares: [[PART:ROT-PMP-IMP-01]]

### [[FAULT:RM-MOT-003]] - Motor overcurrent on start

- Equipment: [[ASSET:HSM-RM-MOT]]
- Severity: medium
- Meaning: Starting current above expected envelope.
- Likely cause: Mechanical binding or supply imbalance.
- Recommended action: Check driven load and supply; investigate before repeated starts.
- Related SOPs: [[SOP:SOP-VIB-001]]
- Related spares: [[PART:RM-MOT-BRG-01]]

### [[FAULT:AGC-HYD-003]] - Hydraulic oil contamination high

- Equipment: [[ASSET:HSM-AGC-HYD]]
- Severity: medium
- Meaning: Particle count above ISO 4406 target.
- Likely cause: Ingress or filter bypass.
- Recommended action: Flush and replace filtration; sample per SOP-OIL-001.
- Related SOPs: [[SOP:SOP-OIL-001]]
- Related spares: [[PART:AGC-SEAL-KIT-01]]

