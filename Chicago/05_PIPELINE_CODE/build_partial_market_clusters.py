"""Combine completed county parcel adapters into a partial Chicago MSA view."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--as-of", default="2026-08-28")
    args = parser.parse_args()

    inputs = [
        args.root / "03_PROCESSED" / "cook_2026_llc_parcels.csv",
        args.root / "03_PROCESSED" / "kendall_20260828_llc_parcels.csv",
    ]
    parcel_rows = [row for path in inputs for row in read_rows(path)]
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in parcel_rows:
        groups[row["owner_mailing_address_key"]].append(row)

    output: list[dict[str, object]] = []
    for key, members in groups.items():
        llcs = sorted({m["legal_owner_normalized"] for m in members})
        parcel_keys = sorted({f"{m['state']}:{m['county']}:{m['parcel_id']}" for m in members})
        counties = sorted({f"{m['county']} {m['state']}" for m in members})
        if len(llcs) < 2 or len(parcel_keys) < 2:
            continue
        first = members[0]
        output.append({
            "owner_mailing_address_key": key,
            "mail_address": first["owner_mailing_address_raw"],
            "mail_city": first["owner_mailing_city_raw"],
            "mail_state": first["owner_mailing_state_raw"],
            "mail_zip": first["owner_mailing_zip_raw"],
            "distinct_llc_count": len(llcs),
            "property_count": len(parcel_keys),
            "county_count": len(counties),
            "counties": " | ".join(counties),
            "llc_names": " | ".join(llcs),
            "parcel_keys": " | ".join(parcel_keys),
            "service_provider_review": "REQUIRED",
            "usps_cass_dpv_status": "NOT_RUN",
            "mailing_status": "RESEARCH_ONLY_NOT_MAIL_READY",
            "coverage_status": "PARTIAL_MSA_COOK_AND_KENDALL_ONLY",
            "as_of_date": args.as_of,
        })
    output.sort(key=lambda r: (-int(r["distinct_llc_count"]), -int(r["property_count"]), str(r["owner_mailing_address_key"])))
    stamp = args.as_of.replace("-", "")
    processed = args.root / "03_PROCESSED" / f"chicago_msa_partial_cook_kendall_{stamp}_address_clusters.csv"
    candidate = args.root / "01_FINAL_OUTPUTS" / f"chicago_msa_partial_cook_kendall_{stamp}_candidate_mailing_RESEARCH_ONLY.csv"
    write_rows(processed, output)
    write_rows(candidate, output)
    print({
        "input_parcels": len(parcel_rows),
        "qualifying_partial_msa_clusters": len(output),
        "cross_county_clusters": sum(int(r["county_count"]) > 1 for r in output),
        "mailing_ready": False,
    })


if __name__ == "__main__":
    main()
