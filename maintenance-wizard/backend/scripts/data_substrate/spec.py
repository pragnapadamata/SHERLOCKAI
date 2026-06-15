"""Single source of truth for the synthetic steel-plant data substrate.

Every artifact -- equipment master, spares, fault catalog, histories, sensor
series, documents, and the data dictionary -- is derived from the registries and
constants defined here. Editing the substrate means editing this file and then
re-running ``make_all``. The module self-validates internal cross-references at
import time, so a typo in an id fails loudly rather than producing incoherent
data.

Domain: Tata Steel Hot Strip Mill (finishing area), framed as a prototype for an
Asset Monitoring & Diagnostic Centre (AMDC) under a Maintenance Technology
Roadmap (MTR). All data is synthetic except the Round 1 hot-rolling CSVs, which
are real and only referenced here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data"

RAW_DOCS = DATA_ROOT / "raw" / "documents"
RAW_STRUCTURED = DATA_ROOT / "raw" / "structured"
RAW_SENSORS = DATA_ROOT / "raw" / "sensors"
ROUND1_DIR = DATA_ROOT / "round1_hotrolling"
DATA_DICT_DIR = DATA_ROOT / "data_dictionary"
PROCESSED_DIR = DATA_ROOT / "processed"

# The whole simulated timeline is anchored here. Shift this one constant to move
# every synthetic timestamp together.
SIMULATION_NOW = datetime(2026, 6, 6, 6, 0, 0)

RANDOM_SEED = 42

# Sensor sampling: 10-minute aggregated features (what an AMDC dashboard persists).
SENSOR_PERIOD_MINUTES = 10
SAMPLES_PER_DAY = 24 * 60 // SENSOR_PERIOD_MINUTES  # 144
WINDOW_WEEKS = 16

# ISO 10816-3 velocity RMS zone boundaries (mm/s) for Class III/IV rotating
# machinery on a rigid foundation. Cited, prototype values.
ISO_RMS_ALERT = 1.4   # zone A/B -> B/C boundary
ISO_RMS_ACTION = 2.8  # zone B/C -> C/D boundary
ISO_RMS_DAMAGE = 4.5  # onset of the damage zone

PROTOTYPE_HEADER = (
    "> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, "
    "do not use operationally.**"
)

# Reference grammar used inside LLM-drafted documents so cross-references are
# both human-readable and machine-checkable.
REFERENCE_PREFIXES = {
    "ASSET": "equipment",
    "FAULT": "fault code",
    "SOP": "standard operating procedure",
    "PART": "spare part",
    "FR": "failure report",
    "MANUAL": "equipment manual",
}


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class Area(StrEnum):
    ROUGHING = "Roughing"
    FINISHING = "Finishing"
    RUNOUT = "Run-out Table"
    COILING = "Coiling"
    UTILITIES = "Utilities"


class EquipType(StrEnum):
    BEARING = "Bearing"
    GEARBOX = "Gearbox"
    MOTOR = "Motor"
    PUMP = "Pump"
    HYDRAULIC = "Hydraulic"
    LUBRICATION = "Lubrication"
    MANDREL = "Mandrel"


class Criticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SpareStatus(StrEnum):
    IN_STOCK = "in_stock"
    ON_ORDER = "on_order"
    NONE = "none"


class Role(StrEnum):
    ENGINEER = "engineer"
    SUPERVISOR = "supervisor"
    PLANT_MANAGER = "plant_manager"
    ANALYST = "analyst"
    SYSTEM = "system"  # the autonomous Maintenance Wizard engine


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

class Asset(BaseModel):
    equipment_id: str
    name: str
    area: Area
    type: EquipType
    manufacturer_code: str
    model_no: str
    install_date: str  # ISO date
    service_hours: int
    mtbf_hours: int
    monitored: bool
    process_criticality: Criticality
    typical_delay_severity_min: int
    spare_availability: SpareStatus
    procurement_lead_time_weeks: int
    notes: str


class SparePart(BaseModel):
    part_id: str
    description: str
    equipment_id: str
    on_hand_qty: int
    spare_availability: SpareStatus
    procurement_lead_time_weeks: int
    supplier_code: str
    unit_cost_inr: int


class FaultCode(BaseModel):
    fault_code: str
    equipment_id: str
    title: str
    meaning: str
    likely_cause: str
    recommended_action: str
    related_sops: list[str]
    related_spares: list[str]
    severity: Criticality


class DocType(StrEnum):
    MANUAL = "manual"
    SOP = "sop"
    FAILURE_REPORT = "failure_report"
    FAULT_CATALOG = "fault_catalog"


class DocSpec(BaseModel):
    doc_id: str
    doc_type: DocType
    title: str
    rel_path: str  # relative to RAW_DOCS
    equipment_id: str | None = None
    required_sections: list[str]
    required_refs: list[str]  # grammar tokens, e.g. "FAULT:F3-GBX-002"
    context_faults: list[str] = []
    context_sops: list[str] = []
    context_spares: list[str] = []
    context_failure_reports: list[str] = []
    inject_positive_coils: bool = False
    extra_brief: str = ""


class ChannelPlan(BaseModel):
    name: str
    unit: str
    baseline: float
    noise_sigma: float
    end_value: float | None = None  # None => flat (no degradation trend)
    decimals: int = 2
    description: str


class AnomalyEvent(BaseModel):
    day: int                    # day offset from window start
    duration_samples: int       # how many consecutive samples it spans
    overrides: dict[str, float] # channel -> forced value
    note: str


class SensorPlan(BaseModel):
    equipment_id: str
    baseline_weeks: int
    degradation_weeks: int
    primary_channel: str  # channel used for ISO regime classification
    channels: list[ChannelPlan]
    anomalies: list[AnomalyEvent] = []


class User(BaseModel):
    user_id: str
    name: str
    role: Role
    area: str
    email: str
    can_write_logbook: bool
    can_acknowledge_alerts: bool


class LogbookEntry(BaseModel):
    entry_id: str
    timestamp: str
    equipment_id: str
    author_user_id: str
    entry_type: str  # observation | action | confirmation
    text: str
    related_fault_code: str | None = None


class HistoryEvent(BaseModel):
    work_order_id: str
    equipment_id: str
    date: str
    type: str  # preventive | corrective | inspection | lubrication | oil_sample | alert
    description: str
    technician: str
    fault_code: str | None = None
    parts_used: str | None = None
    downtime_min: int | None = None
    outcome: str


class DelayEvent(BaseModel):
    delay_id: str
    equipment_id: str
    date: str
    duration_min: int
    category: str
    description: str
    shift: str


class IncidentEvent(BaseModel):
    incident_id: str
    equipment_id: str
    date: str
    severity: Criticality
    description: str
    fault_code: str | None = None
    resolved: bool = True
    related_failure_report: str | None = None


class ProcessIndicator(BaseModel):
    equipment_id: str
    indicator: str
    nominal_value: float
    alert_value: float
    action_value: float
    unit: str
    reference: str


class ColumnSpec(BaseModel):
    name: str
    dtype: str
    unit: str
    nullable: bool
    description: str


class TableSchema(BaseModel):
    name: str
    filename: str
    purpose: str
    source_class: str  # programmatic | real
    columns: list[ColumnSpec]
    notes: str


# --------------------------------------------------------------------------- #
# Equipment master (10 assets; 3 hero + 7 supporting)
# --------------------------------------------------------------------------- #

ASSETS: list[Asset] = [
    Asset(
        equipment_id="HSM-F2-WRB",
        name="F2 finishing stand work-roll bearing (drive side)",
        area=Area.FINISHING, type=EquipType.BEARING,
        manufacturer_code="OEM-A", model_no="A-TRB-4R-220",
        install_date="2019-03-12", service_hours=58200, mtbf_hours=52000,
        monitored=True,
        process_criticality=Criticality.HIGH, typical_delay_severity_min=180,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=2,
        notes="Four-row tapered roller bearing; lubrication-sensitive: vulnerable to bearing distress if a lubrication cycle is missed.",
    ),
    Asset(
        equipment_id="HSM-F3-GBX",
        name="F3 main drive gearbox (herringbone / planetary)",
        area=Area.FINISHING, type=EquipType.GEARBOX,
        manufacturer_code="OEM-B", model_no="B-HGX-900",
        install_date="2017-08-01", service_hours=71500, mtbf_hours=80000,
        monitored=True,
        process_criticality=Criticality.CRITICAL, typical_delay_severity_min=420,
        spare_availability=SpareStatus.ON_ORDER, procurement_lead_time_weeks=8,
        notes="Stage-2 gear set is the wear-critical element: historically the first part to show gear-mesh wear.",
    ),
    Asset(
        equipment_id="HSM-DC-MND",
        name="Down-coiler mandrel and wrapper-roll assembly",
        area=Area.COILING, type=EquipType.MANDREL,
        manufacturer_code="OEM-C", model_no="C-MND-1600",
        install_date="2018-11-20", service_hours=64300, mtbf_hours=70000,
        monitored=True,
        process_criticality=Criticality.HIGH, typical_delay_severity_min=240,
        spare_availability=SpareStatus.ON_ORDER, procurement_lead_time_weeks=6,
        notes="Coils are produced through this asset; surface-defect clusters on coiled product originate here.",
    ),
    Asset(
        equipment_id="HSM-DSC-PMP",
        name="Descaler high-pressure pump",
        area=Area.ROUGHING, type=EquipType.PUMP,
        manufacturer_code="OEM-C", model_no="C-HPP-450",
        install_date="2020-05-30", service_hours=44100, mtbf_hours=40000,
        monitored=False,
        process_criticality=Criticality.MEDIUM, typical_delay_severity_min=90,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=2,
        notes="Plunger-seal wear drives descaling pressure loss.",
    ),
    Asset(
        equipment_id="HSM-RM-MOT",
        name="Roughing-mill main drive motor",
        area=Area.ROUGHING, type=EquipType.MOTOR,
        manufacturer_code="OEM-B", model_no="B-MOT-5000",
        install_date="2016-02-18", service_hours=88600, mtbf_hours=95000,
        monitored=False,
        process_criticality=Criticality.HIGH, typical_delay_severity_min=300,
        spare_availability=SpareStatus.ON_ORDER, procurement_lead_time_weeks=12,
        notes="Stator rewind is a long-lead item; insulation degradation is the main risk.",
    ),
    Asset(
        equipment_id="HSM-ROT-PMP",
        name="Run-out-table cooling pump group",
        area=Area.RUNOUT, type=EquipType.PUMP,
        manufacturer_code="OEM-C", model_no="C-CWP-300",
        install_date="2021-01-10", service_hours=33800, mtbf_hours=45000,
        monitored=False,
        process_criticality=Criticality.MEDIUM, typical_delay_severity_min=60,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=3,
        notes="Cavitation leads to impeller wear; redundant group softens impact.",
    ),
    Asset(
        equipment_id="HSM-AGC-HYD",
        name="Hydraulic Automatic Gauge Control (AGC) system",
        area=Area.FINISHING, type=EquipType.HYDRAULIC,
        manufacturer_code="OEM-B", model_no="B-AGC-HYD-12",
        install_date="2018-06-05", service_hours=66200, mtbf_hours=60000,
        monitored=False,
        process_criticality=Criticality.HIGH, typical_delay_severity_min=150,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=5,
        notes="Servo-valve contamination causes strip-gauge variation.",
    ),
    Asset(
        equipment_id="HSM-F1-WRB",
        name="F1 finishing stand work-roll bearing",
        area=Area.FINISHING, type=EquipType.BEARING,
        manufacturer_code="OEM-A", model_no="A-TRB-4R-220",
        install_date="2019-03-12", service_hours=58200, mtbf_hours=52000,
        monitored=False,
        process_criticality=Criticality.MEDIUM, typical_delay_severity_min=120,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=2,
        notes="Same family as F2; lighter monitoring. Precedent failure in FR-2024-001.",
    ),
    Asset(
        equipment_id="HSM-F4-F7-BRG",
        name="F4-F7 finishing stand bearings (group)",
        area=Area.FINISHING, type=EquipType.BEARING,
        manufacturer_code="OEM-A", model_no="A-TRB-4R-220",
        install_date="2019-04-01", service_hours=57000, mtbf_hours=52000,
        monitored=False,
        process_criticality=Criticality.HIGH, typical_delay_severity_min=200,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=3,
        notes="Grouped entry for plant-level prioritization breadth.",
    ),
    Asset(
        equipment_id="HSM-LUB-UNIT",
        name="Mill central lubrication unit",
        area=Area.UTILITIES, type=EquipType.LUBRICATION,
        manufacturer_code="OEM-C", model_no="C-LUB-CENT-8",
        install_date="2017-09-15", service_hours=72100, mtbf_hours=85000,
        monitored=False,
        process_criticality=Criticality.CRITICAL, typical_delay_severity_min=360,
        spare_availability=SpareStatus.IN_STOCK, procurement_lead_time_weeks=1,
        notes="Single point of supply to multiple stands; filter clogging is the main risk.",
    ),
]


# --------------------------------------------------------------------------- #
# Spare-parts master (18)
# --------------------------------------------------------------------------- #

SPARES: list[SparePart] = [
    SparePart(part_id="GBX-GEAR-SET-01", description="F3 gearbox Stage-2 gear set (pinion + wheel)",
              equipment_id="HSM-F3-GBX", on_hand_qty=0, spare_availability=SpareStatus.ON_ORDER,
              procurement_lead_time_weeks=8, supplier_code="OEM-B", unit_cost_inr=4200000),
    SparePart(part_id="GBX-BRG-SET-01", description="F3 gearbox input-shaft bearing set",
              equipment_id="HSM-F3-GBX", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=6, supplier_code="OEM-B", unit_cost_inr=850000),
    SparePart(part_id="GBX-OIL-FILT-01", description="F3 gearbox oil filter element",
              equipment_id="HSM-F3-GBX", on_hand_qty=4, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=1, supplier_code="OEM-B", unit_cost_inr=12000),
    SparePart(part_id="BRG-F2-TRB-01", description="F2 work-roll four-row tapered roller bearing",
              equipment_id="HSM-F2-WRB", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=2, supplier_code="OEM-A", unit_cost_inr=680000),
    SparePart(part_id="BRG-F1-TRB-01", description="F1 work-roll four-row tapered roller bearing",
              equipment_id="HSM-F1-WRB", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=2, supplier_code="OEM-A", unit_cost_inr=680000),
    SparePart(part_id="BRG-F4F7-TRB-01", description="F4-F7 work-roll bearing (group stock)",
              equipment_id="HSM-F4-F7-BRG", on_hand_qty=2, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=3, supplier_code="OEM-A", unit_cost_inr=680000),
    SparePart(part_id="DC-MND-SEG-01", description="Down-coiler mandrel segment set",
              equipment_id="HSM-DC-MND", on_hand_qty=0, spare_availability=SpareStatus.ON_ORDER,
              procurement_lead_time_weeks=6, supplier_code="OEM-C", unit_cost_inr=1500000),
    SparePart(part_id="DC-WRAP-BRG-01", description="Down-coiler wrapper-roll bearing",
              equipment_id="HSM-DC-MND", on_hand_qty=2, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=3, supplier_code="OEM-A", unit_cost_inr=240000),
    SparePart(part_id="DSC-PMP-SEAL-01", description="Descaler pump high-pressure seal kit",
              equipment_id="HSM-DSC-PMP", on_hand_qty=3, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=2, supplier_code="OEM-C", unit_cost_inr=85000),
    SparePart(part_id="DSC-PMP-PLUNGER-01", description="Descaler pump plunger assembly",
              equipment_id="HSM-DSC-PMP", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=4, supplier_code="OEM-C", unit_cost_inr=210000),
    SparePart(part_id="RM-MOT-BRG-01", description="Roughing motor drive-end bearing",
              equipment_id="HSM-RM-MOT", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=4, supplier_code="OEM-A", unit_cost_inr=320000),
    SparePart(part_id="RM-MOT-WIND-01", description="Roughing motor stator rewind kit",
              equipment_id="HSM-RM-MOT", on_hand_qty=0, spare_availability=SpareStatus.ON_ORDER,
              procurement_lead_time_weeks=12, supplier_code="OEM-B", unit_cost_inr=3800000),
    SparePart(part_id="ROT-PMP-IMP-01", description="Run-out-table pump impeller",
              equipment_id="HSM-ROT-PMP", on_hand_qty=2, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=3, supplier_code="OEM-C", unit_cost_inr=95000),
    SparePart(part_id="AGC-SERVO-VALVE-01", description="AGC servo valve",
              equipment_id="HSM-AGC-HYD", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=5, supplier_code="OEM-B", unit_cost_inr=540000),
    SparePart(part_id="AGC-SEAL-KIT-01", description="AGC cylinder seal kit",
              equipment_id="HSM-AGC-HYD", on_hand_qty=4, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=1, supplier_code="OEM-B", unit_cost_inr=45000),
    SparePart(part_id="LUB-FILT-01", description="Central lubrication unit filter element",
              equipment_id="HSM-LUB-UNIT", on_hand_qty=8, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=1, supplier_code="OEM-C", unit_cost_inr=9000),
    SparePart(part_id="LUB-PUMP-01", description="Central lubrication transfer pump",
              equipment_id="HSM-LUB-UNIT", on_hand_qty=1, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=4, supplier_code="OEM-C", unit_cost_inr=180000),
    SparePart(part_id="GREASE-EP2-DRUM", description="EP2 lithium-complex grease (drum)",
              equipment_id="HSM-LUB-UNIT", on_hand_qty=10, spare_availability=SpareStatus.IN_STOCK,
              procurement_lead_time_weeks=1, supplier_code="OEM-C", unit_cost_inr=22000),
]


# --------------------------------------------------------------------------- #
# Fault catalog (25)
# --------------------------------------------------------------------------- #

FAULTS: list[FaultCode] = [
    # F3 gearbox -- Story A
    FaultCode(fault_code="F3-GBX-002", equipment_id="HSM-F3-GBX",
              title="Rising gear-mesh sidebands with oil iron-particle trend",
              meaning="Gear-mesh-frequency sidebands and oil Fe particle count rising together over weeks.",
              likely_cause="Stage-2 gear-tooth pitting progressing toward tooth fracture.",
              recommended_action="Confirm by vibration spectrum and oil analysis; plan Stage-2 gear set replacement before fracture.",
              related_sops=["SOP-GBX-001", "SOP-OIL-001", "SOP-VIB-001"],
              related_spares=["GBX-GEAR-SET-01"], severity=Criticality.CRITICAL),
    FaultCode(fault_code="F3-GBX-001", equipment_id="HSM-F3-GBX",
              title="Gearbox oil over-temperature",
              meaning="Oil temperature exceeds normal operating band.",
              likely_cause="Cooler fouling, low oil level, or excessive load.",
              recommended_action="Check cooler and oil level; sample oil per SOP-OIL-001.",
              related_sops=["SOP-OIL-001"], related_spares=["GBX-OIL-FILT-01"],
              severity=Criticality.MEDIUM),
    FaultCode(fault_code="F3-GBX-003", equipment_id="HSM-F3-GBX",
              title="Gearbox low oil level",
              meaning="Lubricant level below minimum sight-glass mark.",
              likely_cause="Leak at seal or drain; top-up overdue.",
              recommended_action="Inspect seals, top up, and re-sample oil.",
              related_sops=["SOP-OIL-001"], related_spares=["GBX-OIL-FILT-01"],
              severity=Criticality.HIGH),
    FaultCode(fault_code="F3-GBX-004", equipment_id="HSM-F3-GBX",
              title="Gearbox broadband vibration high",
              meaning="Overall vibration RMS in ISO action zone.",
              likely_cause="Advanced gear or bearing damage, or misalignment.",
              recommended_action="Stop at next opportunity; inspect per SOP-GBX-001.",
              related_sops=["SOP-GBX-001", "SOP-VIB-001"],
              related_spares=["GBX-GEAR-SET-01", "GBX-BRG-SET-01"], severity=Criticality.CRITICAL),
    # F2 bearing -- Story B
    FaultCode(fault_code="F2-WRB-001", equipment_id="HSM-F2-WRB",
              title="Bearing temperature and vibration rising with inner-race signature",
              meaning="Bearing temperature and vibration RMS rising together with a ball-pass inner-race (BPFI) signature.",
              likely_cause="Lubrication starvation leading to inner-race spalling.",
              recommended_action="Perform immediate lubrication check per SOP-LUB-001; plan bearing replacement per SOP-BRG-001.",
              related_sops=["SOP-LUB-001", "SOP-BRG-001", "SOP-VIB-001"],
              related_spares=["BRG-F2-TRB-01", "GREASE-EP2-DRUM"], severity=Criticality.HIGH),
    FaultCode(fault_code="F2-WRB-002", equipment_id="HSM-F2-WRB",
              title="Bearing over-temperature trip",
              meaning="Bearing temperature crosses the protective trip threshold.",
              likely_cause="Loss of lubrication or advanced spalling.",
              recommended_action="Stop the stand; do not restart before lubrication and inspection.",
              related_sops=["SOP-LUB-001", "SOP-BRG-001"],
              related_spares=["BRG-F2-TRB-01"], severity=Criticality.CRITICAL),
    FaultCode(fault_code="F2-WRB-003", equipment_id="HSM-F2-WRB",
              title="Bearing housing looseness",
              meaning="Sub-harmonic and harmonic vibration pattern suggesting mechanical looseness.",
              likely_cause="Loose housing bolts or worn fit.",
              recommended_action="Torque-check housing; inspect fits per SOP-BRG-001.",
              related_sops=["SOP-BRG-001"], related_spares=["BRG-F2-TRB-01"],
              severity=Criticality.MEDIUM),
    # Down-coiler -- Story C
    FaultCode(fault_code="DC-MND-001", equipment_id="HSM-DC-MND",
              title="Mandrel segment wear",
              meaning="Mandrel segment clearance beyond tolerance.",
              likely_cause="Abrasive wear of segment faces over service life.",
              recommended_action="Measure segment clearance per SOP-MND-001; replace segment set if out of tolerance.",
              related_sops=["SOP-MND-001"], related_spares=["DC-MND-SEG-01"],
              severity=Criticality.HIGH),
    FaultCode(fault_code="DC-MND-002", equipment_id="HSM-DC-MND",
              title="Wrapper-roll bearing vibration",
              meaning="Intermittent wrapper-roll bearing vibration ticks.",
              likely_cause="Early wrapper-roll bearing degradation.",
              recommended_action="Trend vibration; replace wrapper-roll bearing at next planned stop.",
              related_sops=["SOP-BRG-001", "SOP-VIB-001"],
              related_spares=["DC-WRAP-BRG-01"], severity=Criticality.MEDIUM),
    FaultCode(fault_code="DC-PROC-001", equipment_id="HSM-DC-MND",
              title="Alpha surface-defect cluster on coiled product",
              meaning="Cluster of Alpha surface defects on finished coils correlated with upstream multi-stage process parameters.",
              likely_cause="Process-parameter excursions interacting with equipment condition (assessed by the Phase 3 defect model).",
              recommended_action="Review process parameters for flagged coils; cross-check mandrel and wrapper-roll condition.",
              related_sops=["SOP-MND-001"], related_spares=["DC-WRAP-BRG-01"],
              severity=Criticality.MEDIUM),
    # Supporting assets
    FaultCode(fault_code="DSC-PMP-001", equipment_id="HSM-DSC-PMP",
              title="Low descaling pressure",
              meaning="Header pressure below descaling setpoint.",
              likely_cause="Plunger-seal wear or valve leakage.",
              recommended_action="Replace seal kit; inspect plunger.",
              related_sops=["SOP-BRG-001"],
              related_spares=["DSC-PMP-SEAL-01", "DSC-PMP-PLUNGER-01"], severity=Criticality.MEDIUM),
    FaultCode(fault_code="RM-MOT-001", equipment_id="HSM-RM-MOT",
              title="Stator winding over-temperature",
              meaning="Winding RTD temperature trending high.",
              likely_cause="Insulation degradation or cooling loss.",
              recommended_action="Reduce load; plan insulation test and rewind.",
              related_sops=["SOP-VIB-001"], related_spares=["RM-MOT-WIND-01"],
              severity=Criticality.HIGH),
    FaultCode(fault_code="RM-MOT-002", equipment_id="HSM-RM-MOT",
              title="Motor drive-end bearing vibration",
              meaning="Drive-end bearing vibration rising.",
              likely_cause="Bearing wear.",
              recommended_action="Trend and replace drive-end bearing.",
              related_sops=["SOP-BRG-001", "SOP-VIB-001"],
              related_spares=["RM-MOT-BRG-01"], severity=Criticality.MEDIUM),
    FaultCode(fault_code="ROT-PMP-001", equipment_id="HSM-ROT-PMP",
              title="Cooling pump cavitation",
              meaning="Pump cavitation signature with flow fluctuation.",
              likely_cause="Suction restriction or low NPSH.",
              recommended_action="Check suction strainer; inspect impeller.",
              related_sops=["SOP-VIB-001"], related_spares=["ROT-PMP-IMP-01"],
              severity=Criticality.MEDIUM),
    FaultCode(fault_code="AGC-HYD-001", equipment_id="HSM-AGC-HYD",
              title="Servo-valve contamination causing gauge variation",
              meaning="Strip-gauge variation correlated with sluggish servo-valve response.",
              likely_cause="Hydraulic fluid contamination.",
              recommended_action="Flush system; replace servo valve if response is out of spec.",
              related_sops=["SOP-OIL-001"], related_spares=["AGC-SERVO-VALVE-01"],
              severity=Criticality.HIGH),
    FaultCode(fault_code="AGC-HYD-002", equipment_id="HSM-AGC-HYD",
              title="Low hydraulic pressure",
              meaning="AGC supply pressure below setpoint.",
              likely_cause="Pump wear or internal leakage.",
              recommended_action="Check pump and seals; replace seal kit.",
              related_sops=["SOP-OIL-001"], related_spares=["AGC-SEAL-KIT-01"],
              severity=Criticality.MEDIUM),
    FaultCode(fault_code="F1-WRB-001", equipment_id="HSM-F1-WRB",
              title="F1 bearing vibration rising",
              meaning="F1 work-roll bearing vibration trending up.",
              likely_cause="Lubrication or early spalling, as seen on the F-stand family.",
              recommended_action="Lubricate per SOP-LUB-001; trend and plan replacement.",
              related_sops=["SOP-LUB-001", "SOP-BRG-001"],
              related_spares=["BRG-F1-TRB-01"], severity=Criticality.MEDIUM),
    FaultCode(fault_code="LUB-UNIT-001", equipment_id="HSM-LUB-UNIT",
              title="Lubrication filter clogging / low downstream flow",
              meaning="Downstream lubrication flow falling with rising filter differential pressure.",
              likely_cause="Filter element clogged.",
              recommended_action="Replace filter element per SOP-LUB-001.",
              related_sops=["SOP-LUB-001"], related_spares=["LUB-FILT-01"],
              severity=Criticality.HIGH),
    FaultCode(fault_code="LUB-UNIT-002", equipment_id="HSM-LUB-UNIT",
              title="Lubrication reservoir low level",
              meaning="Grease/oil reservoir below minimum.",
              likely_cause="Consumption without refill or a leak.",
              recommended_action="Refill and inspect for leaks.",
              related_sops=["SOP-LUB-001"], related_spares=["GREASE-EP2-DRUM"],
              severity=Criticality.MEDIUM),
    FaultCode(fault_code="F4F7-BRG-001", equipment_id="HSM-F4-F7-BRG",
              title="F4-F7 bearing vibration (group)",
              meaning="One of the F4-F7 stand bearings shows rising vibration.",
              likely_cause="Lubrication or wear on a finishing-stand bearing.",
              recommended_action="Identify the stand; lubricate and trend.",
              related_sops=["SOP-LUB-001", "SOP-VIB-001"],
              related_spares=["BRG-F4F7-TRB-01"], severity=Criticality.MEDIUM),
    FaultCode(fault_code="DSC-PMP-002", equipment_id="HSM-DSC-PMP",
              title="Descaler pump vibration",
              meaning="Pump vibration rising.",
              likely_cause="Bearing or coupling wear.",
              recommended_action="Inspect coupling and bearings.",
              related_sops=["SOP-VIB-001"], related_spares=["DSC-PMP-PLUNGER-01"],
              severity=Criticality.LOW),
    FaultCode(fault_code="ROT-PMP-002", equipment_id="HSM-ROT-PMP",
              title="Cooling pump seal leak",
              meaning="Visible leak at pump mechanical seal.",
              likely_cause="Seal wear.",
              recommended_action="Replace mechanical seal.",
              related_sops=["SOP-BRG-001"], related_spares=["ROT-PMP-IMP-01"],
              severity=Criticality.LOW),
    FaultCode(fault_code="RM-MOT-003", equipment_id="HSM-RM-MOT",
              title="Motor overcurrent on start",
              meaning="Starting current above expected envelope.",
              likely_cause="Mechanical binding or supply imbalance.",
              recommended_action="Check driven load and supply; investigate before repeated starts.",
              related_sops=["SOP-VIB-001"], related_spares=["RM-MOT-BRG-01"],
              severity=Criticality.MEDIUM),
    FaultCode(fault_code="AGC-HYD-003", equipment_id="HSM-AGC-HYD",
              title="Hydraulic oil contamination high",
              meaning="Particle count above ISO 4406 target.",
              likely_cause="Ingress or filter bypass.",
              recommended_action="Flush and replace filtration; sample per SOP-OIL-001.",
              related_sops=["SOP-OIL-001"], related_spares=["AGC-SEAL-KIT-01"],
              severity=Criticality.MEDIUM),
]


# --------------------------------------------------------------------------- #
# Sensor plans (3 hero assets)
# --------------------------------------------------------------------------- #

SENSOR_PLANS: list[SensorPlan] = [
    SensorPlan(
        equipment_id="HSM-F3-GBX", baseline_weeks=8, degradation_weeks=8,
        primary_channel="vibration_rms_mm_s",
        channels=[
            ChannelPlan(name="vibration_rms_mm_s", unit="mm/s", baseline=1.20,
                        noise_sigma=0.04, end_value=2.50, decimals=3,
                        description="Overall velocity RMS (ISO 10816-3)."),
            ChannelPlan(name="gmf_sideband_db", unit="dB", baseline=-32.0,
                        noise_sigma=0.5, end_value=-20.0, decimals=2,
                        description="Gear-mesh-frequency sideband amplitude."),
            ChannelPlan(name="oil_fe_ppm", unit="ppm", baseline=18.0,
                        noise_sigma=0.6, end_value=34.0, decimals=1,
                        description="Oil iron-particle concentration."),
            ChannelPlan(name="oil_temp_C", unit="degC", baseline=52.0,
                        noise_sigma=0.4, end_value=55.0, decimals=1,
                        description="Gearbox oil temperature."),
            ChannelPlan(name="motor_current_A", unit="A", baseline=600.0,
                        noise_sigma=6.0, end_value=615.0, decimals=1,
                        description="Drive motor current."),
        ],
    ),
    SensorPlan(
        equipment_id="HSM-F2-WRB", baseline_weeks=10, degradation_weeks=6,
        primary_channel="vibration_rms_mm_s",
        channels=[
            ChannelPlan(name="vibration_rms_mm_s", unit="mm/s", baseline=1.00,
                        noise_sigma=0.04, end_value=2.00, decimals=3,
                        description="Overall velocity RMS (ISO 10816-3)."),
            ChannelPlan(name="vibration_peak_mm_s", unit="mm/s", baseline=1.60,
                        noise_sigma=0.06, end_value=3.20, decimals=3,
                        description="Peak velocity."),
            ChannelPlan(name="bpfi_amplitude_g", unit="g", baseline=0.05,
                        noise_sigma=0.005, end_value=0.45, decimals=3,
                        description="Ball-pass inner-race defect-frequency amplitude."),
            ChannelPlan(name="bearing_temp_C", unit="degC", baseline=45.0,
                        noise_sigma=0.5, end_value=53.0, decimals=1,
                        description="Bearing housing temperature."),
            ChannelPlan(name="motor_current_A", unit="A", baseline=480.0,
                        noise_sigma=5.0, end_value=490.0, decimals=1,
                        description="Stand drive current."),
        ],
        anomalies=[
            AnomalyEvent(day=108, duration_samples=18,
                         overrides={"vibration_rms_mm_s": 4.70, "vibration_peak_mm_s": 7.50,
                                    "bpfi_amplitude_g": 0.90, "bearing_temp_C": 60.0},
                         note="Sudden vibration step change - suspected inner-race defect."),
        ],
    ),
    SensorPlan(
        equipment_id="HSM-DC-MND", baseline_weeks=16, degradation_weeks=0,
        primary_channel="vibration_rms_mm_s",
        channels=[
            ChannelPlan(name="vibration_rms_mm_s", unit="mm/s", baseline=1.10,
                        noise_sigma=0.05, end_value=None, decimals=3,
                        description="Overall velocity RMS (ISO 10816-3)."),
            ChannelPlan(name="bearing_temp_C", unit="degC", baseline=40.0,
                        noise_sigma=0.5, end_value=None, decimals=1,
                        description="Wrapper-roll bearing temperature."),
            ChannelPlan(name="hydraulic_pressure_bar", unit="bar", baseline=180.0,
                        noise_sigma=1.5, end_value=None, decimals=1,
                        description="Mandrel hydraulic pressure."),
            ChannelPlan(name="motor_current_A", unit="A", baseline=350.0,
                        noise_sigma=4.0, end_value=None, decimals=1,
                        description="Coiler drive current."),
            ChannelPlan(name="coil_tension_kN", unit="kN", baseline=120.0,
                        noise_sigma=2.0, end_value=None, decimals=1,
                        description="Strip coiling tension."),
        ],
        anomalies=[
            AnomalyEvent(day=30, duration_samples=3, overrides={"vibration_rms_mm_s": 1.80},
                         note="Wrapper-roll vibration tick."),
            AnomalyEvent(day=75, duration_samples=3, overrides={"vibration_rms_mm_s": 1.90},
                         note="Wrapper-roll vibration tick."),
            AnomalyEvent(day=100, duration_samples=3, overrides={"vibration_rms_mm_s": 1.70},
                         note="Wrapper-roll vibration tick."),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# Process condition indicators (reference-only, one+ row per asset)
# --------------------------------------------------------------------------- #

PROCESS_INDICATORS: list[ProcessIndicator] = [
    ProcessIndicator(equipment_id="HSM-F2-WRB", indicator="vibration_rms", nominal_value=1.0,
                     alert_value=ISO_RMS_ALERT, action_value=ISO_RMS_ACTION, unit="mm/s",
                     reference="ISO 10816-3 Class III/IV"),
    ProcessIndicator(equipment_id="HSM-F2-WRB", indicator="bearing_temp", nominal_value=45.0,
                     alert_value=55.0, action_value=65.0, unit="degC", reference="OEM-A manual"),
    ProcessIndicator(equipment_id="HSM-F3-GBX", indicator="vibration_rms", nominal_value=1.2,
                     alert_value=ISO_RMS_ALERT, action_value=ISO_RMS_ACTION, unit="mm/s",
                     reference="ISO 10816-3 Class III/IV"),
    ProcessIndicator(equipment_id="HSM-F3-GBX", indicator="oil_fe", nominal_value=18.0,
                     alert_value=30.0, action_value=40.0, unit="ppm", reference="OEM-B manual"),
    ProcessIndicator(equipment_id="HSM-F3-GBX", indicator="oil_temp", nominal_value=52.0,
                     alert_value=60.0, action_value=70.0, unit="degC", reference="OEM-B manual"),
    ProcessIndicator(equipment_id="HSM-DC-MND", indicator="vibration_rms", nominal_value=1.1,
                     alert_value=ISO_RMS_ALERT, action_value=ISO_RMS_ACTION, unit="mm/s",
                     reference="ISO 10816-3 Class III/IV"),
    ProcessIndicator(equipment_id="HSM-DC-MND", indicator="hydraulic_pressure", nominal_value=180.0,
                     alert_value=160.0, action_value=150.0, unit="bar", reference="OEM-C manual"),
    ProcessIndicator(equipment_id="HSM-DSC-PMP", indicator="header_pressure", nominal_value=380.0,
                     alert_value=340.0, action_value=300.0, unit="bar", reference="OEM-C manual"),
    ProcessIndicator(equipment_id="HSM-RM-MOT", indicator="winding_temp", nominal_value=95.0,
                     alert_value=120.0, action_value=140.0, unit="degC", reference="OEM-B manual"),
    ProcessIndicator(equipment_id="HSM-ROT-PMP", indicator="flow", nominal_value=100.0,
                     alert_value=85.0, action_value=70.0, unit="pct", reference="OEM-C manual"),
    ProcessIndicator(equipment_id="HSM-AGC-HYD", indicator="supply_pressure", nominal_value=210.0,
                     alert_value=190.0, action_value=175.0, unit="bar", reference="OEM-B manual"),
    ProcessIndicator(equipment_id="HSM-F1-WRB", indicator="vibration_rms", nominal_value=1.0,
                     alert_value=ISO_RMS_ALERT, action_value=ISO_RMS_ACTION, unit="mm/s",
                     reference="ISO 10816-3 Class III/IV"),
    ProcessIndicator(equipment_id="HSM-F4-F7-BRG", indicator="vibration_rms", nominal_value=1.0,
                     alert_value=ISO_RMS_ALERT, action_value=ISO_RMS_ACTION, unit="mm/s",
                     reference="ISO 10816-3 Class III/IV"),
    ProcessIndicator(equipment_id="HSM-LUB-UNIT", indicator="downstream_flow", nominal_value=100.0,
                     alert_value=80.0, action_value=65.0, unit="pct", reference="OEM-C manual"),
]


# --------------------------------------------------------------------------- #
# Users (6) and logbook seed (15)
# --------------------------------------------------------------------------- #

USERS: list[User] = [
    User(user_id="U-ENG-01", name="R. Mahato", role=Role.ENGINEER, area="Finishing",
         email="r.mahato@example-hsm.local", can_write_logbook=True, can_acknowledge_alerts=True),
    User(user_id="U-ENG-02", name="S. Iyer", role=Role.ENGINEER, area="Coiling",
         email="s.iyer@example-hsm.local", can_write_logbook=True, can_acknowledge_alerts=True),
    User(user_id="U-SUP-01", name="A. Bose", role=Role.SUPERVISOR, area="Finishing",
         email="a.bose@example-hsm.local", can_write_logbook=True, can_acknowledge_alerts=True),
    User(user_id="U-SUP-02", name="P. Singh", role=Role.SUPERVISOR, area="Roughing",
         email="p.singh@example-hsm.local", can_write_logbook=True, can_acknowledge_alerts=True),
    User(user_id="U-PM-01", name="K. Nair", role=Role.PLANT_MANAGER, area="Hot Strip Mill",
         email="k.nair@example-hsm.local", can_write_logbook=True, can_acknowledge_alerts=True),
    User(user_id="U-AN-01", name="T. Das", role=Role.ANALYST, area="AMDC",
         email="t.das@example-hsm.local", can_write_logbook=False, can_acknowledge_alerts=False),
    User(user_id="U-SYS-AMDC", name="Maintenance Wizard (autonomous)", role=Role.SYSTEM,
         area="AMDC", email="amdc-system@example-hsm.local",
         can_write_logbook=True, can_acknowledge_alerts=False),
]

LOGBOOK_SEED: list[LogbookEntry] = [
    LogbookEntry(entry_id="LB-0001", timestamp="2026-05-22T09:15:00", equipment_id="HSM-F3-GBX",
                 author_user_id="U-ENG-01", entry_type="observation",
                 text="F3 gearbox vibration sidebands rising; oil Fe up to ~30 ppm on last sample.",
                 related_fault_code="F3-GBX-002"),
    LogbookEntry(entry_id="LB-0002", timestamp="2026-05-22T16:40:00", equipment_id="HSM-F3-GBX",
                 author_user_id="U-SUP-01", entry_type="confirmation",
                 text="Confirmed F3-GBX-002 trend with AMDC. Raising spare query for gear set.",
                 related_fault_code="F3-GBX-002"),
    LogbookEntry(entry_id="LB-0003", timestamp="2026-05-30T22:05:00", equipment_id="HSM-F2-WRB",
                 author_user_id="U-ENG-01", entry_type="observation",
                 text="F2 bearing sudden vibration step on night shift; temperature climbing.",
                 related_fault_code="F2-WRB-001"),
    LogbookEntry(entry_id="LB-0004", timestamp="2026-05-31T07:30:00", equipment_id="HSM-F2-WRB",
                 author_user_id="U-SUP-01", entry_type="action",
                 text="Lubrication check ordered on F2 work-roll bearing; spare confirmed in stock.",
                 related_fault_code="F2-WRB-001"),
    LogbookEntry(entry_id="LB-0005", timestamp="2026-04-20T11:00:00", equipment_id="HSM-LUB-UNIT",
                 author_user_id="U-ENG-01", entry_type="observation",
                 text="Central lubrication route to F-stands disrupted during shift; manual top-up partial.",
                 related_fault_code="LUB-UNIT-001"),
    LogbookEntry(entry_id="LB-0006", timestamp="2026-03-10T13:20:00", equipment_id="HSM-DC-MND",
                 author_user_id="U-ENG-02", entry_type="observation",
                 text="Wrapper-roll vibration tick during coil build; no action needed yet.",
                 related_fault_code="DC-MND-002"),
    LogbookEntry(entry_id="LB-0007", timestamp="2026-02-15T08:45:00", equipment_id="HSM-DSC-PMP",
                 author_user_id="U-SUP-02", entry_type="observation",
                 text="Descaling pressure slightly low at start of campaign; monitoring.",
                 related_fault_code="DSC-PMP-001"),
    LogbookEntry(entry_id="LB-0008", timestamp="2026-05-05T10:10:00", equipment_id="HSM-AGC-HYD",
                 author_user_id="U-ENG-01", entry_type="observation",
                 text="Minor gauge variation on thin gauges; suspect servo-valve response.",
                 related_fault_code="AGC-HYD-001"),
    LogbookEntry(entry_id="LB-0009", timestamp="2026-05-23T09:00:00", equipment_id="HSM-F3-GBX",
                 author_user_id="U-AN-01", entry_type="observation",
                 text="AMDC: F3 sideband trend consistent with Stage-2 pitting; RUL estimate pending.",
                 related_fault_code="F3-GBX-002"),
    LogbookEntry(entry_id="LB-0010", timestamp="2026-06-01T15:30:00", equipment_id="HSM-F3-GBX",
                 author_user_id="U-PM-01", entry_type="confirmation",
                 text="Approved spare-procurement query for F3 gear set given lead time concern.",
                 related_fault_code="F3-GBX-002"),
    LogbookEntry(entry_id="LB-0011", timestamp="2026-04-02T12:00:00", equipment_id="HSM-RM-MOT",
                 author_user_id="U-SUP-02", entry_type="observation",
                 text="Roughing motor winding temperature a few degrees above usual under load.",
                 related_fault_code="RM-MOT-001"),
    LogbookEntry(entry_id="LB-0012", timestamp="2026-03-28T18:25:00", equipment_id="HSM-ROT-PMP",
                 author_user_id="U-ENG-02", entry_type="action",
                 text="Cleaned suction strainer on ROT pump group after flow dip.",
                 related_fault_code="ROT-PMP-001"),
    LogbookEntry(entry_id="LB-0013", timestamp="2026-05-12T14:50:00", equipment_id="HSM-DC-MND",
                 author_user_id="U-ENG-02", entry_type="observation",
                 text="Coil quality review flagged a small Alpha-defect cluster; logged for analysis.",
                 related_fault_code="DC-PROC-001"),
    LogbookEntry(entry_id="LB-0014", timestamp="2026-02-20T09:35:00", equipment_id="HSM-LUB-UNIT",
                 author_user_id="U-ENG-01", entry_type="action",
                 text="Replaced central lubrication filter element; differential pressure back to normal.",
                 related_fault_code="LUB-UNIT-001"),
    LogbookEntry(entry_id="LB-0015", timestamp="2026-06-02T06:15:00", equipment_id="HSM-F2-WRB",
                 author_user_id="U-AN-01", entry_type="observation",
                 text="AMDC alert raised automatically on F2 bearing step change overnight.",
                 related_fault_code="F2-WRB-001"),
]


# --------------------------------------------------------------------------- #
# Anchor history / delay / incident events (story-critical; filler added by the
# structured generator around these)
# --------------------------------------------------------------------------- #

ANCHOR_HISTORY: list[HistoryEvent] = [
    HistoryEvent(work_order_id="WO-2025-1180", equipment_id="HSM-F3-GBX", date="2025-12-15",
                 type="oil_sample", description="Routine gearbox oil sample; Fe = 16 ppm, within limits.",
                 technician="U-ENG-01", fault_code=None, parts_used=None, downtime_min=0,
                 outcome="normal"),
    HistoryEvent(work_order_id="WO-2026-0142", equipment_id="HSM-F3-GBX", date="2026-02-10",
                 type="inspection", description="Routine vibration check; overall RMS 1.3 mm/s, normal.",
                 technician="U-ENG-01", fault_code=None, parts_used=None, downtime_min=0,
                 outcome="normal"),
    HistoryEvent(work_order_id="WO-2026-0511", equipment_id="HSM-F3-GBX", date="2026-05-22",
                 type="alert", description="Vibration sidebands and oil Fe trending up; flagged Stage-2 pitting.",
                 technician="U-AN-01", fault_code="F3-GBX-002", parts_used=None, downtime_min=0,
                 outcome="spare query raised for GBX-GEAR-SET-01"),
    HistoryEvent(work_order_id="WO-2026-0540", equipment_id="HSM-F2-WRB", date="2026-06-02",
                 type="corrective", description="Auto-alert on sudden bearing vibration step; lubrication check.",
                 technician="U-ENG-01", fault_code="F2-WRB-001",
                 parts_used="GREASE-EP2-DRUM", downtime_min=45,
                 outcome="root cause: missed lubrication cycle week of 2026-04-20"),
    HistoryEvent(work_order_id="WO-2024-0902", equipment_id="HSM-F3-GBX", date="2024-09-18",
                 type="corrective", description="Stage-2 gear-tooth fracture; emergency gear set replacement.",
                 technician="U-ENG-01", fault_code="F3-GBX-002",
                 parts_used="GBX-GEAR-SET-01", downtime_min=540,
                 outcome="replaced; see FR-2024-002"),
    HistoryEvent(work_order_id="WO-2024-0233", equipment_id="HSM-F1-WRB", date="2024-03-05",
                 type="corrective", description="Inner-race spalling after lubrication starvation; bearing replaced.",
                 technician="U-ENG-01", fault_code="F1-WRB-001",
                 parts_used="BRG-F1-TRB-01", downtime_min=210,
                 outcome="replaced; see FR-2024-001"),
    HistoryEvent(work_order_id="WO-2025-0307", equipment_id="HSM-DSC-PMP", date="2025-04-22",
                 type="corrective", description="Descaling pressure loss; seal kit replaced.",
                 technician="U-SUP-02", fault_code="DSC-PMP-001",
                 parts_used="DSC-PMP-SEAL-01", downtime_min=120,
                 outcome="replaced; see FR-2025-001"),
    HistoryEvent(work_order_id="WO-2025-0815", equipment_id="HSM-DC-MND", date="2025-09-30",
                 type="corrective", description="Wrapper-roll bearing degradation and Alpha-defect cluster review.",
                 technician="U-ENG-02", fault_code="DC-MND-002",
                 parts_used="DC-WRAP-BRG-01", downtime_min=180,
                 outcome="replaced; see FR-2025-002"),
]

ANCHOR_DELAYS: list[DelayEvent] = [
    DelayEvent(delay_id="DL-2026-0610", equipment_id="HSM-F3-GBX", date="2026-05-25",
               duration_min=20, category="inspection", description="Operator-requested F3 vibration inspection.", shift="A"),
    DelayEvent(delay_id="DL-2026-0617", equipment_id="HSM-F3-GBX", date="2026-05-29",
               duration_min=35, category="inspection", description="F3 gearbox oil sampling stop.", shift="B"),
    DelayEvent(delay_id="DL-2026-0625", equipment_id="HSM-F3-GBX", date="2026-06-03",
               duration_min=15, category="inspection", description="F3 vibration re-check after trend alert.", shift="A"),
    DelayEvent(delay_id="DL-2026-0631", equipment_id="HSM-F2-WRB", date="2026-06-01",
               duration_min=10, category="mechanical", description="Minor F2 vibration alarm acknowledged.", shift="C"),
    DelayEvent(delay_id="DL-2026-0634", equipment_id="HSM-F2-WRB", date="2026-06-02",
               duration_min=45, category="mechanical", description="F2 bearing step-change auto-alert; lubrication check.", shift="C"),
]

ANCHOR_INCIDENTS: list[IncidentEvent] = [
    IncidentEvent(incident_id="INC-2024-031", equipment_id="HSM-F3-GBX", date="2024-09-18",
                  severity=Criticality.CRITICAL, description="Stage-2 gear-tooth fracture, 9-hour outage.",
                  fault_code="F3-GBX-002", resolved=True, related_failure_report="FR-2024-002"),
    IncidentEvent(incident_id="INC-2024-009", equipment_id="HSM-F1-WRB", date="2024-03-05",
                  severity=Criticality.HIGH, description="F1 work-roll bearing inner-race spalling.",
                  fault_code="F1-WRB-001", resolved=True, related_failure_report="FR-2024-001"),
    IncidentEvent(incident_id="INC-2025-014", equipment_id="HSM-DSC-PMP", date="2025-04-22",
                  severity=Criticality.MEDIUM, description="Descaling pressure loss event.",
                  fault_code="DSC-PMP-001", resolved=True, related_failure_report="FR-2025-001"),
    IncidentEvent(incident_id="INC-2025-028", equipment_id="HSM-DC-MND", date="2025-09-30",
                  severity=Criticality.MEDIUM, description="Wrapper-roll bearing degradation with defect cluster.",
                  fault_code="DC-MND-002", resolved=True, related_failure_report="FR-2025-002"),
    IncidentEvent(incident_id="INC-2026-019", equipment_id="HSM-F3-GBX", date="2026-05-22",
                  severity=Criticality.HIGH, description="Stage-2 pitting trend detected; replacement planned.",
                  fault_code="F3-GBX-002", resolved=False, related_failure_report="FR-2024-002"),
    IncidentEvent(incident_id="INC-2026-024", equipment_id="HSM-F2-WRB", date="2026-06-02",
                  severity=Criticality.HIGH, description="Sudden F2 bearing vibration step detected by AMDC.",
                  fault_code="F2-WRB-001", resolved=False, related_failure_report="FR-2024-001"),
]


# --------------------------------------------------------------------------- #
# Document specs (LLM-drafted, validated, then frozen)
# --------------------------------------------------------------------------- #

DOCS: list[DocSpec] = [
    DocSpec(doc_id="HSM-F3-GBX_manual", doc_type=DocType.MANUAL,
            title="F3 Main Drive Gearbox - Equipment Manual",
            rel_path="manuals/HSM-F3-GBX_manual.md", equipment_id="HSM-F3-GBX",
            required_sections=["Overview", "Specifications", "Maintenance", "Troubleshooting"],
            required_refs=["ASSET:HSM-F3-GBX", "FAULT:F3-GBX-002", "SOP:SOP-GBX-001",
                           "SOP:SOP-OIL-001", "PART:GBX-GEAR-SET-01"],
            context_faults=["F3-GBX-001", "F3-GBX-002", "F3-GBX-003", "F3-GBX-004"],
            context_sops=["SOP-GBX-001", "SOP-OIL-001", "SOP-VIB-001"],
            context_spares=["GBX-GEAR-SET-01", "GBX-BRG-SET-01", "GBX-OIL-FILT-01"]),
    DocSpec(doc_id="HSM-F2-WRB_manual", doc_type=DocType.MANUAL,
            title="F2 Work-Roll Bearing - Equipment Manual",
            rel_path="manuals/HSM-F2-WRB_manual.md", equipment_id="HSM-F2-WRB",
            required_sections=["Overview", "Specifications", "Maintenance", "Troubleshooting"],
            required_refs=["ASSET:HSM-F2-WRB", "FAULT:F2-WRB-001", "SOP:SOP-BRG-001",
                           "SOP:SOP-LUB-001", "PART:BRG-F2-TRB-01"],
            context_faults=["F2-WRB-001", "F2-WRB-002", "F2-WRB-003"],
            context_sops=["SOP-BRG-001", "SOP-LUB-001", "SOP-VIB-001"],
            context_spares=["BRG-F2-TRB-01", "GREASE-EP2-DRUM"]),
    DocSpec(doc_id="HSM-DC-MND_manual", doc_type=DocType.MANUAL,
            title="Down-Coiler Mandrel and Wrapper Roll - Equipment Manual",
            rel_path="manuals/HSM-DC-MND_manual.md", equipment_id="HSM-DC-MND",
            required_sections=["Overview", "Specifications", "Maintenance", "Troubleshooting"],
            required_refs=["ASSET:HSM-DC-MND", "FAULT:DC-MND-001", "FAULT:DC-MND-002",
                           "SOP:SOP-MND-001", "PART:DC-MND-SEG-01", "PART:DC-WRAP-BRG-01"],
            context_faults=["DC-MND-001", "DC-MND-002", "DC-PROC-001"],
            context_sops=["SOP-MND-001", "SOP-BRG-001", "SOP-VIB-001"],
            context_spares=["DC-MND-SEG-01", "DC-WRAP-BRG-01"]),
    DocSpec(doc_id="SOP-BRG-001", doc_type=DocType.SOP,
            title="SOP - Work-Roll Bearing Replacement",
            rel_path="sops/SOP-BRG-001_bearing_replacement.md",
            required_sections=["Purpose", "Safety", "Tools and Spares", "Procedure", "Acceptance"],
            required_refs=["SOP:SOP-BRG-001", "PART:BRG-F2-TRB-01"],
            context_spares=["BRG-F2-TRB-01", "GREASE-EP2-DRUM"],
            context_faults=["F2-WRB-001"]),
    DocSpec(doc_id="SOP-GBX-001", doc_type=DocType.SOP,
            title="SOP - Gearbox Inspection",
            rel_path="sops/SOP-GBX-001_gear_inspection.md",
            required_sections=["Purpose", "Safety", "Tools and Spares", "Procedure", "Acceptance"],
            required_refs=["SOP:SOP-GBX-001", "ASSET:HSM-F3-GBX", "FAULT:F3-GBX-002"],
            context_faults=["F3-GBX-002", "F3-GBX-004"],
            context_spares=["GBX-GEAR-SET-01"]),
    DocSpec(doc_id="SOP-LUB-001", doc_type=DocType.SOP,
            title="SOP - Lubrication Procedure",
            rel_path="sops/SOP-LUB-001_lubrication_procedure.md",
            required_sections=["Purpose", "Safety", "Materials", "Procedure", "Frequency"],
            required_refs=["SOP:SOP-LUB-001", "PART:GREASE-EP2-DRUM"],
            context_spares=["GREASE-EP2-DRUM"],
            context_faults=["F2-WRB-001", "LUB-UNIT-001"]),
    DocSpec(doc_id="SOP-OIL-001", doc_type=DocType.SOP,
            title="SOP - Oil Sampling and Analysis (ISO 4406)",
            rel_path="sops/SOP-OIL-001_oil_sampling_iso4406.md",
            required_sections=["Purpose", "Safety", "Equipment", "Procedure", "Interpretation"],
            required_refs=["SOP:SOP-OIL-001", "FAULT:F3-GBX-002"],
            context_faults=["F3-GBX-001", "F3-GBX-002"],
            extra_brief="Reference ISO 4406 cleanliness coding and oil Fe particle trending."),
    DocSpec(doc_id="SOP-VIB-001", doc_type=DocType.SOP,
            title="SOP - Vibration Measurement (ISO 10816-3)",
            rel_path="sops/SOP-VIB-001_vibration_measurement_iso10816.md",
            required_sections=["Purpose", "Safety", "Equipment", "Procedure", "Zones"],
            required_refs=["SOP:SOP-VIB-001"],
            context_faults=["F2-WRB-001", "F3-GBX-002"],
            extra_brief=(f"State the ISO 10816-3 velocity RMS zone boundaries used here: "
                         f"alert at {ISO_RMS_ALERT} mm/s, action at {ISO_RMS_ACTION} mm/s, "
                         f"damage onset at {ISO_RMS_DAMAGE} mm/s.")),
    DocSpec(doc_id="SOP-MND-001", doc_type=DocType.SOP,
            title="SOP - Down-Coiler Mandrel Inspection",
            rel_path="sops/SOP-MND-001_mandrel_inspection.md",
            required_sections=["Purpose", "Safety", "Tools and Spares", "Procedure", "Acceptance"],
            required_refs=["SOP:SOP-MND-001", "ASSET:HSM-DC-MND", "FAULT:DC-MND-001"],
            context_faults=["DC-MND-001", "DC-MND-002"],
            context_spares=["DC-MND-SEG-01", "DC-WRAP-BRG-01"]),
    DocSpec(doc_id="FR-2024-001", doc_type=DocType.FAILURE_REPORT,
            title="Failure Analysis Report FR-2024-001 - F1 Work-Roll Bearing Lubrication Starvation",
            rel_path="failure_reports/FR-2024-001_F2_bearing_lub_starvation.md", equipment_id="HSM-F1-WRB",
            required_sections=["Summary", "Timeline", "Root Cause", "Corrective Action", "Lessons"],
            required_refs=["FR:FR-2024-001", "ASSET:HSM-F1-WRB", "FAULT:F1-WRB-001",
                           "SOP:SOP-LUB-001", "PART:BRG-F1-TRB-01"],
            context_faults=["F1-WRB-001", "F2-WRB-001"],
            context_sops=["SOP-LUB-001", "SOP-BRG-001"],
            context_spares=["BRG-F1-TRB-01", "GREASE-EP2-DRUM"],
            extra_brief=("Precedent for the F-stand bearing family: a missed lubrication cycle led to "
                         "inner-race spalling. This precedent informs the current F2 case (Story B).")),
    DocSpec(doc_id="FR-2024-002", doc_type=DocType.FAILURE_REPORT,
            title="Failure Analysis Report FR-2024-002 - F3 Gearbox Stage-2 Gear-Tooth Fracture",
            rel_path="failure_reports/FR-2024-002_F3_gear_pitting_fracture.md", equipment_id="HSM-F3-GBX",
            required_sections=["Summary", "Timeline", "Root Cause", "Corrective Action", "Lessons"],
            required_refs=["FR:FR-2024-002", "ASSET:HSM-F3-GBX", "FAULT:F3-GBX-002",
                           "SOP:SOP-GBX-001", "PART:GBX-GEAR-SET-01"],
            context_faults=["F3-GBX-002"],
            context_sops=["SOP-GBX-001", "SOP-OIL-001"],
            context_spares=["GBX-GEAR-SET-01"],
            extra_brief=("Precedent for the current F3 case (Story A): the same Fe-particle and "
                         "vibration-sideband progression preceded a tooth fracture and a 9-hour outage. "
                         "Iron particle count rose from ~18 ppm to ~34 ppm; replacement gear set lead time is 8 weeks.")),
    DocSpec(doc_id="FR-2025-001", doc_type=DocType.FAILURE_REPORT,
            title="Failure Analysis Report FR-2025-001 - Descaler Pump Seal Failure",
            rel_path="failure_reports/FR-2025-001_descaler_pump_seal.md", equipment_id="HSM-DSC-PMP",
            required_sections=["Summary", "Timeline", "Root Cause", "Corrective Action", "Lessons"],
            required_refs=["FR:FR-2025-001", "ASSET:HSM-DSC-PMP", "FAULT:DSC-PMP-001",
                           "PART:DSC-PMP-SEAL-01"],
            context_faults=["DSC-PMP-001"],
            context_spares=["DSC-PMP-SEAL-01", "DSC-PMP-PLUNGER-01"]),
    DocSpec(doc_id="FR-2025-002", doc_type=DocType.FAILURE_REPORT,
            title="Failure Analysis Report FR-2025-002 - Down-Coiler Wrapper-Roll Bearing and Alpha-Defect Cluster",
            rel_path="failure_reports/FR-2025-002_DC_wrapper_bearing.md", equipment_id="HSM-DC-MND",
            required_sections=["Summary", "Timeline", "Root Cause", "Corrective Action", "Lessons"],
            required_refs=["FR:FR-2025-002", "ASSET:HSM-DC-MND", "FAULT:DC-MND-002",
                           "FAULT:DC-PROC-001", "PART:DC-WRAP-BRG-01"],
            context_faults=["DC-MND-002", "DC-PROC-001"],
            context_spares=["DC-WRAP-BRG-01"],
            inject_positive_coils=True,
            extra_brief=("Links wrapper-roll bearing degradation to a cluster of Alpha surface defects on "
                         "coiled product. Reference the specific defect-positive Coil IDs provided. The Alpha-defect "
                         "risk model is trained in Phase 3 and exposed as a tool.")),
    DocSpec(doc_id="fault_codes", doc_type=DocType.FAULT_CATALOG,
            title="Fault / Error Code Catalog",
            rel_path="fault_catalog/fault_codes.md",
            required_sections=["Overview", "Catalog"],
            required_refs=[f"FAULT:{f.fault_code}" for f in FAULTS],
            context_faults=[f.fault_code for f in FAULTS]),
]


# --------------------------------------------------------------------------- #
# Table schemas (drive both CSV generation and the data dictionary)
# --------------------------------------------------------------------------- #

def _col(name: str, dtype: str, unit: str, nullable: bool, desc: str) -> ColumnSpec:
    return ColumnSpec(name=name, dtype=dtype, unit=unit, nullable=nullable, description=desc)


TABLE_SCHEMAS: list[TableSchema] = [
    TableSchema(name="equipment_master", filename="equipment_master.csv",
                purpose="Master record of every monitored and supporting asset with the four prioritization dimensions.",
                source_class="programmatic", columns=[
                    _col("equipment_id", "str", "-", False, "Stable asset identifier (primary key)."),
                    _col("name", "str", "-", False, "Human-readable asset name."),
                    _col("area", "str", "-", False, "Plant area."),
                    _col("type", "str", "-", False, "Equipment type."),
                    _col("manufacturer_code", "str", "-", False, "Synthetic OEM tag (OEM-A/B/C)."),
                    _col("model_no", "str", "-", False, "Synthetic model number."),
                    _col("install_date", "date", "-", False, "Commissioning date."),
                    _col("service_hours", "int", "h", False, "Hours in service."),
                    _col("mtbf_hours", "int", "h", False, "Mean time between failures for the family."),
                    _col("monitored", "bool", "-", False, "True for the three hero assets with sensor data."),
                    _col("process_criticality", "str", "-", False, "Prioritization: low|medium|high|critical."),
                    _col("typical_delay_severity_min", "int", "min", False, "Prioritization: typical minutes lost per failure."),
                    _col("spare_availability", "str", "-", False, "Prioritization: in_stock|on_order|none."),
                    _col("procurement_lead_time_weeks", "int", "week", False, "Prioritization: spare lead time."),
                    _col("notes", "str", "-", False, "Engineer note."),
                ], notes="The four prioritization dimensions are populated for all ten assets."),
    TableSchema(name="spare_parts_master", filename="spare_parts_master.csv",
                purpose="Spare parts mapped to equipment, with stock, availability, and lead time.",
                source_class="programmatic", columns=[
                    _col("part_id", "str", "-", False, "Spare part identifier (primary key)."),
                    _col("description", "str", "-", False, "Part description."),
                    _col("equipment_id", "str", "-", False, "Mapped asset (foreign key to equipment_master)."),
                    _col("on_hand_qty", "int", "ea", False, "Quantity on hand."),
                    _col("spare_availability", "str", "-", False, "in_stock|on_order|none."),
                    _col("procurement_lead_time_weeks", "int", "week", False, "Procurement lead time."),
                    _col("supplier_code", "str", "-", False, "Synthetic supplier tag."),
                    _col("unit_cost_inr", "int", "INR", False, "Synthetic unit cost."),
                ], notes="GBX-GEAR-SET-01 (lead 8 weeks, on_order) and BRG-F2-TRB-01 (in_stock) are story-critical."),
    TableSchema(name="fault_catalog", filename="fault_catalog.csv",
                purpose="Canonical fault/error codes with cause, action, and cross-links to SOPs and spares.",
                source_class="programmatic", columns=[
                    _col("fault_code", "str", "-", False, "Fault code (primary key)."),
                    _col("equipment_id", "str", "-", False, "Affected asset."),
                    _col("title", "str", "-", False, "Short title."),
                    _col("meaning", "str", "-", False, "What the fault indicates."),
                    _col("likely_cause", "str", "-", False, "Probable root cause."),
                    _col("recommended_action", "str", "-", False, "Recommended response."),
                    _col("related_sops", "str", "-", False, "Semicolon-separated SOP ids."),
                    _col("related_spares", "str", "-", False, "Semicolon-separated spare part ids."),
                    _col("severity", "str", "-", False, "low|medium|high|critical."),
                ], notes="related_sops and related_spares resolve to SOP documents and spare_parts_master rows."),
    TableSchema(name="maintenance_history", filename="maintenance_history.csv",
                purpose="Past work orders per asset, including the story-critical anchor events.",
                source_class="programmatic", columns=[
                    _col("work_order_id", "str", "-", False, "Work order id (primary key)."),
                    _col("equipment_id", "str", "-", False, "Asset."),
                    _col("date", "date", "-", False, "Work order date."),
                    _col("type", "str", "-", False, "preventive|corrective|inspection|lubrication|oil_sample|alert."),
                    _col("description", "str", "-", False, "What was done or observed."),
                    _col("technician", "str", "-", False, "User id of the technician."),
                    _col("fault_code", "str", "-", True, "Related fault code, if any."),
                    _col("parts_used", "str", "-", True, "Spare part id used, if any."),
                    _col("downtime_min", "int", "min", True, "Downtime incurred."),
                    _col("outcome", "str", "-", False, "Result."),
                ], notes="The F2 lubrication schedule deliberately omits the cycle around 2026-04-20 (Story B root cause)."),
    TableSchema(name="delay_logs", filename="delay_logs.csv",
                purpose="Equipment delay events supporting delay-severity prioritization.",
                source_class="programmatic", columns=[
                    _col("delay_id", "str", "-", False, "Delay id (primary key)."),
                    _col("equipment_id", "str", "-", False, "Asset."),
                    _col("date", "date", "-", False, "Date of delay."),
                    _col("duration_min", "int", "min", False, "Delay duration."),
                    _col("category", "str", "-", False, "mechanical|electrical|hydraulic|process|inspection."),
                    _col("description", "str", "-", False, "Delay description."),
                    _col("shift", "str", "-", False, "Shift A|B|C."),
                ], notes="Recent F3 inspection delays and F2 alarms are anchor events tied to the hero stories."),
    TableSchema(name="incident_records", filename="incident_records.csv",
                purpose="Historical breakdown summaries, cross-linked to failure reports.",
                source_class="programmatic", columns=[
                    _col("incident_id", "str", "-", False, "Incident id (primary key)."),
                    _col("equipment_id", "str", "-", False, "Asset."),
                    _col("date", "date", "-", False, "Incident date."),
                    _col("severity", "str", "-", False, "low|medium|high|critical."),
                    _col("description", "str", "-", False, "Incident description."),
                    _col("fault_code", "str", "-", True, "Related fault code."),
                    _col("resolved", "bool", "-", False, "Whether resolved."),
                    _col("related_failure_report", "str", "-", True, "Related failure report id."),
                ], notes="related_failure_report resolves to a document under raw/documents/failure_reports."),
    TableSchema(name="process_conditions", filename="process_conditions.csv",
                purpose="Reference normal/alert/action operating values per asset indicator.",
                source_class="programmatic", columns=[
                    _col("equipment_id", "str", "-", False, "Asset."),
                    _col("indicator", "str", "-", False, "Condition indicator name."),
                    _col("nominal_value", "float", "varies", False, "Normal operating value."),
                    _col("alert_value", "float", "varies", False, "Alert threshold."),
                    _col("action_value", "float", "varies", False, "Action threshold."),
                    _col("unit", "str", "-", False, "Unit of measure."),
                    _col("reference", "str", "-", False, "Source of the threshold."),
                ], notes="Vibration thresholds follow ISO 10816-3; others follow synthetic OEM manuals."),
    TableSchema(name="coil_log", filename="coil_log.csv",
                purpose="Maps every Round 1 CoilID to the down-coiler and binds it into the plant narrative.",
                source_class="programmatic", columns=[
                    _col("coil_id", "str", "-", False, "Round 1 CoilID (primary key)."),
                    _col("source", "str", "-", False, "Round 1 split: train|test."),
                    _col("produced_at", "datetime", "-", False, "Synthetic production timestamp."),
                    _col("assigned_asset_id", "str", "-", False, "Always HSM-DC-MND."),
                    _col("grade", "str", "-", False, "Synthetic steel grade."),
                    _col("thickness_mm", "float", "mm", False, "Synthetic coil thickness."),
                    _col("width_mm", "float", "mm", False, "Synthetic coil width."),
                    _col("alpha_label", "int", "-", True, "Round 1 Y (1=defect, 0=no defect); null for test split."),
                    _col("alpha_risk_score", "float", "-", True, "Populated by the Phase 3 model; null here."),
                ], notes="All 1,691 CoilIDs (1,352 train + 339 test) are mapped. alpha_label comes from real Round 1 Y."),
    TableSchema(name="users", filename="users.csv",
                purpose="Role metadata for later role-based views and logbook permissions.",
                source_class="programmatic", columns=[
                    _col("user_id", "str", "-", False, "User id (primary key)."),
                    _col("name", "str", "-", False, "Display name."),
                    _col("role", "str", "-", False, "engineer|supervisor|plant_manager|analyst."),
                    _col("area", "str", "-", False, "Area of responsibility."),
                    _col("email", "str", "-", False, "Synthetic contact."),
                    _col("can_write_logbook", "bool", "-", False, "Logbook write permission."),
                    _col("can_acknowledge_alerts", "bool", "-", False, "Alert acknowledge permission."),
                ], notes="Two engineers, two supervisors, one plant manager, one read-only analyst, "
                         "and one autonomous system user (U-SYS-AMDC) for machine-generated entries."),
    TableSchema(name="logbook_seed", filename="logbook_seed.csv",
                purpose="Pre-populated digital logbook entries seeding the optional logbook enhancement.",
                source_class="programmatic", columns=[
                    _col("entry_id", "str", "-", False, "Entry id (primary key)."),
                    _col("timestamp", "datetime", "-", False, "Entry timestamp."),
                    _col("equipment_id", "str", "-", False, "Asset."),
                    _col("author_user_id", "str", "-", False, "Author (foreign key to users)."),
                    _col("entry_type", "str", "-", False, "observation|action|confirmation."),
                    _col("text", "str", "-", False, "Entry text."),
                    _col("related_fault_code", "str", "-", True, "Related fault code, if any."),
                ], notes="Entries reference the hero stories and the same fault codes used elsewhere."),
]


# --------------------------------------------------------------------------- #
# Registries and lookups
# --------------------------------------------------------------------------- #

ASSETS_BY_ID = {a.equipment_id: a for a in ASSETS}
SPARES_BY_ID = {s.part_id: s for s in SPARES}
FAULTS_BY_CODE = {f.fault_code: f for f in FAULTS}
DOCS_BY_ID = {d.doc_id: d for d in DOCS}
SOP_IDS = {d.doc_id for d in DOCS if d.doc_type is DocType.SOP}
MANUAL_IDS = {d.doc_id for d in DOCS if d.doc_type is DocType.MANUAL}
FAILURE_REPORT_IDS = {d.doc_id for d in DOCS if d.doc_type is DocType.FAILURE_REPORT}


def window_start() -> datetime:
    """First timestamp of the sensor window."""

    return SIMULATION_NOW - timedelta(days=WINDOW_WEEKS * 7) + timedelta(minutes=SENSOR_PERIOD_MINUTES)


def resolve_reference(token: str) -> bool:
    """Return True if a ``TYPE:id`` reference token resolves to a known entity."""

    if ":" not in token:
        return False
    kind, _, ident = token.partition(":")
    kind = kind.strip().upper()
    ident = ident.strip()
    if kind == "ASSET":
        return ident in ASSETS_BY_ID
    if kind == "FAULT":
        return ident in FAULTS_BY_CODE
    if kind == "PART":
        return ident in SPARES_BY_ID
    if kind == "SOP":
        return ident in SOP_IDS
    if kind == "MANUAL":
        return ident in MANUAL_IDS or ident in ASSETS_BY_ID
    if kind == "FR":
        return ident in FAILURE_REPORT_IDS
    return False


# --------------------------------------------------------------------------- #
# Internal consistency check (runs at import)
# --------------------------------------------------------------------------- #

def _validate_internal_consistency() -> None:
    errors: list[str] = []

    # Unique ids
    for label, ids in [
        ("asset", [a.equipment_id for a in ASSETS]),
        ("spare", [s.part_id for s in SPARES]),
        ("fault", [f.fault_code for f in FAULTS]),
        ("doc", [d.doc_id for d in DOCS]),
        ("user", [u.user_id for u in USERS]),
        ("logbook", [e.entry_id for e in LOGBOOK_SEED]),
    ]:
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate {label} id detected")

    # Spares map to real assets
    for s in SPARES:
        if s.equipment_id not in ASSETS_BY_ID:
            errors.append(f"spare {s.part_id} maps to unknown asset {s.equipment_id}")

    # Faults map to real assets and reference real SOPs/spares
    for f in FAULTS:
        if f.equipment_id not in ASSETS_BY_ID:
            errors.append(f"fault {f.fault_code} maps to unknown asset {f.equipment_id}")
        for sop in f.related_sops:
            if sop not in SOP_IDS:
                errors.append(f"fault {f.fault_code} references unknown SOP {sop}")
        for part in f.related_spares:
            if part not in SPARES_BY_ID:
                errors.append(f"fault {f.fault_code} references unknown spare {part}")

    # Sensor plans reference real assets
    for p in SENSOR_PLANS:
        if p.equipment_id not in ASSETS_BY_ID:
            errors.append(f"sensor plan references unknown asset {p.equipment_id}")

    # Doc required_refs resolve
    for d in DOCS:
        for ref in d.required_refs:
            if not resolve_reference(ref):
                errors.append(f"doc {d.doc_id} has unresolved required ref {ref}")
        for code in d.context_faults:
            if code not in FAULTS_BY_CODE:
                errors.append(f"doc {d.doc_id} context fault {code} unknown")
        for part in d.context_spares:
            if part not in SPARES_BY_ID:
                errors.append(f"doc {d.doc_id} context spare {part} unknown")

    # Anchor events reference real assets and faults
    for h in ANCHOR_HISTORY:
        if h.equipment_id not in ASSETS_BY_ID:
            errors.append(f"history {h.work_order_id} unknown asset {h.equipment_id}")
        if h.fault_code and h.fault_code not in FAULTS_BY_CODE:
            errors.append(f"history {h.work_order_id} unknown fault {h.fault_code}")
    for i in ANCHOR_INCIDENTS:
        if i.fault_code and i.fault_code not in FAULTS_BY_CODE:
            errors.append(f"incident {i.incident_id} unknown fault {i.fault_code}")
        if i.related_failure_report and i.related_failure_report not in FAILURE_REPORT_IDS:
            errors.append(f"incident {i.incident_id} unknown failure report {i.related_failure_report}")

    if errors:
        raise ValueError("spec.py internal consistency errors:\n  - " + "\n  - ".join(errors))


_validate_internal_consistency()
