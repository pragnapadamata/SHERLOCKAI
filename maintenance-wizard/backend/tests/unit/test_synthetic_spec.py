"""Spec invariants: counts, id uniqueness, and reference resolution."""

from __future__ import annotations

from backend.scripts.data_substrate import spec


def test_asset_and_entity_counts():
    assert len(spec.ASSETS) == 10
    assert sum(1 for a in spec.ASSETS if a.monitored) == 3  # three hero assets
    assert len(spec.SPARES) == 18
    assert len(spec.FAULTS) >= 20
    assert len(spec.SENSOR_PLANS) == 3
    assert len(spec.DOCS) == 14


def test_ids_are_unique():
    for ids in (
        [a.equipment_id for a in spec.ASSETS],
        [s.part_id for s in spec.SPARES],
        [f.fault_code for f in spec.FAULTS],
        [d.doc_id for d in spec.DOCS],
        [u.user_id for u in spec.USERS],
    ):
        assert len(ids) == len(set(ids))


def test_every_fault_cross_reference_resolves():
    for f in spec.FAULTS:
        assert f.equipment_id in spec.ASSETS_BY_ID
        for sop in f.related_sops:
            assert sop in spec.SOP_IDS
        for part in f.related_spares:
            assert part in spec.SPARES_BY_ID


def test_doc_required_references_resolve():
    for d in spec.DOCS:
        for ref in d.required_refs:
            assert spec.resolve_reference(ref), f"{d.doc_id}: {ref}"


def test_resolve_reference_rejects_unknown_and_descriptive_tokens():
    assert spec.resolve_reference("ASSET:HSM-F3-GBX")
    assert spec.resolve_reference("FAULT:F3-GBX-002")
    assert not spec.resolve_reference("FAULT:does-not-exist")
    assert not spec.resolve_reference("ASSET:equipment")  # the legend-misuse bug
    assert not spec.resolve_reference("nonsense")


def test_all_assets_carry_four_prioritization_dimensions():
    severities = set(spec.Criticality)
    statuses = set(spec.SpareStatus)
    for a in spec.ASSETS:
        assert a.process_criticality in severities
        assert a.typical_delay_severity_min >= 0
        assert a.spare_availability in statuses
        assert a.procurement_lead_time_weeks >= 0


def test_story_a_lead_time_anchor():
    assert spec.SPARES_BY_ID["GBX-GEAR-SET-01"].procurement_lead_time_weeks == 8
    assert spec.ASSETS_BY_ID["HSM-F3-GBX"].procurement_lead_time_weeks == 8
    assert "GBX-GEAR-SET-01" in spec.FAULTS_BY_CODE["F3-GBX-002"].related_spares
