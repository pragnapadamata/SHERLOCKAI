> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Failure Analysis Report FR-2025-002 - Down-Coiler Wrapper-Roll Bearing and Alpha-Defect Cluster

## Summary
This failure analysis report [[FR:FR-2025-002]] investigates the root cause of the wrapper-roll bearing vibration and Alpha surface-defect cluster on coiled product, specifically on Coil IDs 1015, 1080, 1083, 1110, 1153, and 1181. The issue is associated with the down-coiler mandrel and wrapper-roll assembly [[ASSET:HSM-DC-MND]]. The failure is categorized as a medium-severity fault, with two related fault codes: [[FAULT:DC-MND-002]] for wrapper-roll bearing vibration and [[FAULT:DC-PROC-001]] for Alpha surface-defect cluster.

## Timeline
The wrapper-roll bearing vibration was first detected on November 10, 2024, during a routine vibration check. The Alpha surface-defect cluster was identified on November 15, 2024, after a quality control inspection of the coiled product. The defects were correlated with process-parameter excursions and equipment condition, as assessed by the Phase 3 defect model.

## Root Cause
The root cause of the failure is attributed to the early degradation of the wrapper-roll bearing [[PART:DC-WRAP-BRG-01]], which led to intermittent vibration ticks. This, in turn, contributed to the formation of Alpha surface defects on the coiled product. The process-parameter excursions and equipment condition also played a significant role in the development of the defect cluster.

## Corrective Action
To address the issue, it is recommended to replace the wrapper-roll bearing [[PART:DC-WRAP-BRG-01]] at the next planned stop. Additionally, process parameters should be reviewed for the flagged coils, and the mandrel and wrapper-roll condition should be cross-checked. The related standard operating procedures (SOPs), such as SOP-BRG-001, SOP-VIB-001, and SOP-MND-001, should be followed to ensure proper maintenance and inspection of the equipment.

## Lessons
This failure highlights the importance of regular vibration checks and quality control inspections to detect potential issues early. It also emphasizes the need for proper maintenance and replacement of critical spare parts, such as the wrapper-roll bearing [[PART:DC-WRAP-BRG-01]]. Furthermore, the correlation between process-parameter excursions and equipment condition underscores the importance of monitoring and controlling these factors to prevent similar failures in the future. The Alpha-defect risk model, trained in Phase 3, can be used as a tool to predict and prevent similar defects. The failure is also related to another fault code [[FAULT:DC-PROC-001]], which should be considered in the corrective action plan. The asset [[ASSET:HSM-DC-MND]] should be continuously monitored to prevent similar failures.
