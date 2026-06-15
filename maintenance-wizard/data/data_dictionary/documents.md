> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Documents (`data/raw/documents/`)

**Source class.** LLM-drafted (generate_documents.py) from spec slices, validated
for cross-reference coherence, then frozen as committed source artifacts.

## Reference grammar

Documents cross-reference entities with machine-checkable tokens that the
validator resolves against the spec:

- `[[ASSET:id]]` -> equipment
- `[[FAULT:id]]` -> fault code
- `[[SOP:id]]` -> standard operating procedure
- `[[PART:id]]` -> spare part
- `[[FR:id]]` -> failure report
- `[[MANUAL:id]]` -> equipment manual

## Document set

| Doc id | Type | Title | Path | Required references |
| --- | --- | --- | --- | --- |
| `HSM-F3-GBX_manual` | manual | F3 Main Drive Gearbox - Equipment Manual | `manuals/HSM-F3-GBX_manual.md` | `ASSET:HSM-F3-GBX`, `FAULT:F3-GBX-002`, `SOP:SOP-GBX-001`, `SOP:SOP-OIL-001`, `PART:GBX... |
| `HSM-F2-WRB_manual` | manual | F2 Work-Roll Bearing - Equipment Manual | `manuals/HSM-F2-WRB_manual.md` | `ASSET:HSM-F2-WRB`, `FAULT:F2-WRB-001`, `SOP:SOP-BRG-001`, `SOP:SOP-LUB-001`, `PART:BRG... |
| `HSM-DC-MND_manual` | manual | Down-Coiler Mandrel and Wrapper Roll - Equipment Manual | `manuals/HSM-DC-MND_manual.md` | `ASSET:HSM-DC-MND`, `FAULT:DC-MND-001`, `FAULT:DC-MND-002`, `SOP:SOP-MND-001`, `PART:DC... |
| `SOP-BRG-001` | sop | SOP - Work-Roll Bearing Replacement | `sops/SOP-BRG-001_bearing_replacement.md` | `SOP:SOP-BRG-001`, `PART:BRG-F2-TRB-01` |
| `SOP-GBX-001` | sop | SOP - Gearbox Inspection | `sops/SOP-GBX-001_gear_inspection.md` | `SOP:SOP-GBX-001`, `ASSET:HSM-F3-GBX`, `FAULT:F3-GBX-002` |
| `SOP-LUB-001` | sop | SOP - Lubrication Procedure | `sops/SOP-LUB-001_lubrication_procedure.md` | `SOP:SOP-LUB-001`, `PART:GREASE-EP2-DRUM` |
| `SOP-OIL-001` | sop | SOP - Oil Sampling and Analysis (ISO 4406) | `sops/SOP-OIL-001_oil_sampling_iso4406.md` | `SOP:SOP-OIL-001`, `FAULT:F3-GBX-002` |
| `SOP-VIB-001` | sop | SOP - Vibration Measurement (ISO 10816-3) | `sops/SOP-VIB-001_vibration_measurement_iso10816.md` | `SOP:SOP-VIB-001` |
| `SOP-MND-001` | sop | SOP - Down-Coiler Mandrel Inspection | `sops/SOP-MND-001_mandrel_inspection.md` | `SOP:SOP-MND-001`, `ASSET:HSM-DC-MND`, `FAULT:DC-MND-001` |
| `FR-2024-001` | failure_report | Failure Analysis Report FR-2024-001 - F1 Work-Roll Bearing Lubrication Starvation | `failure_reports/FR-2024-001_F2_bearing_lub_starvation.md` | `FR:FR-2024-001`, `ASSET:HSM-F1-WRB`, `FAULT:F1-WRB-001`, `SOP:SOP-LUB-001`, `PART:BRG-... |
| `FR-2024-002` | failure_report | Failure Analysis Report FR-2024-002 - F3 Gearbox Stage-2 Gear-Tooth Fracture | `failure_reports/FR-2024-002_F3_gear_pitting_fracture.md` | `FR:FR-2024-002`, `ASSET:HSM-F3-GBX`, `FAULT:F3-GBX-002`, `SOP:SOP-GBX-001`, `PART:GBX-... |
| `FR-2025-001` | failure_report | Failure Analysis Report FR-2025-001 - Descaler Pump Seal Failure | `failure_reports/FR-2025-001_descaler_pump_seal.md` | `FR:FR-2025-001`, `ASSET:HSM-DSC-PMP`, `FAULT:DSC-PMP-001`, `PART:DSC-PMP-SEAL-01` |
| `FR-2025-002` | failure_report | Failure Analysis Report FR-2025-002 - Down-Coiler Wrapper-Roll Bearing and Alpha-Defect Cluster | `failure_reports/FR-2025-002_DC_wrapper_bearing.md` | `FR:FR-2025-002`, `ASSET:HSM-DC-MND`, `FAULT:DC-MND-002`, `FAULT:DC-PROC-001`, `PART:DC... |
| `fault_codes` | fault_catalog | Fault / Error Code Catalog | `fault_catalog/fault_codes.md` | `FAULT:F3-GBX-002`, `FAULT:F3-GBX-001`, `FAULT:F3-GBX-003`, `FAULT:F3-GBX-004`, `FAULT:... |
