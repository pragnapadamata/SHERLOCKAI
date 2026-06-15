"""Build the data substrate end to end.

Programmatic artifacts (structured CSVs, sensor parquet, the Round 1 profile, and
the data dictionary) are regenerated deterministically on every run. The prose
documents are drafted once and frozen, so they are only rebuilt when you pass
``--with-docs`` (and only overwritten with ``--force-docs``). Validation always
runs last and is the correctness gate.

Usage:
    python -m backend.scripts.data_substrate.make_all                # programmatic + validate
    python -m backend.scripts.data_substrate.make_all --with-docs    # also draft missing docs
    python -m backend.scripts.data_substrate.make_all --with-docs --force-docs  # redraft all docs
"""

from __future__ import annotations

import argparse
import sys

from backend.scripts.data_substrate import (
    generate_data_dictionary,
    generate_documents,
    generate_sensors,
    generate_structured,
    profile_round1,
    validate_coherence,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Phase 1 data substrate.")
    parser.add_argument("--with-docs", action="store_true",
                        help="Also draft prose documents via the LLM (skips existing).")
    parser.add_argument("--force-docs", action="store_true",
                        help="With --with-docs, redraft documents even if they exist.")
    args = parser.parse_args()

    print("== structured CSVs ==")
    for name, count in generate_structured.generate_all().items():
        print(f"  {name}: {count} rows")

    print("== sensor parquet ==")
    for equipment_id, count in generate_sensors.generate_all().items():
        print(f"  {equipment_id}: {count} samples")

    print("== Round 1 profile ==")
    profile = profile_round1.run()
    print(f"  train {profile['train_rows']}x{profile['train_cols']}, "
          f"test {profile['test_rows']}x{profile['test_cols']}, "
          f"positives {profile['target_positives']} ({profile['target_positive_fraction']:.2%})")

    print("== data dictionary ==")
    written = generate_data_dictionary.generate_all()
    print(f"  {len(written)} files")

    print("== fault catalog document (programmatic) ==")
    print(f"  fault_codes.md: {generate_documents.render_fault_catalog()}")

    if args.with_docs:
        print("== documents (LLM) ==")
        for doc_id, status in generate_documents.generate_all(force=args.force_docs).items():
            print(f"  {doc_id}: {status}")

    print("== validation ==")
    return validate_coherence.main()


if __name__ == "__main__":
    sys.exit(main())
