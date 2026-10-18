"""Download and cluster Cook County LLC-owned parcels by owner mailing address.

This is a research-stage adapter for the generic master specification. It does
not certify addresses for postage and does not infer ownership from situs data.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


DATASET_ID = "3723-97qp"
API_URL = f"https://datacatalog.cookcountyil.gov/resource/{DATASET_ID}.json"
FIELDS = [
    "pin",
    "year",
    "prop_address_full",
    "prop_address_city_name",
    "prop_address_state",
    "prop_address_zipcode_1",
    "owner_address_name",
    "owner_address_full",
    "owner_address_city_name",
    "owner_address_state",
    "owner_address_zipcode_1",
    "row_id",
]

NON_ALNUM = re.compile(r"[^A-Z0-9#]+")
SPACE = re.compile(r"\s+")


def clean(value: object) -> str:
    return SPACE.sub(" ", str(value or "").strip())


def normalize_name(value: object) -> str:
    text = clean(value).upper()
    text = re.sub(r"[,.]", "", text)
    return SPACE.sub(" ", text).strip()


def normalize_address_part(value: object) -> str:
    text = clean(value).upper()
    text = NON_ALNUM.sub(" ", text)
    replacements = {
        " STREET ": " ST ", " AVENUE ": " AVE ", " ROAD ": " RD ",
        " BOULEVARD ": " BLVD ", " DRIVE ": " DR ", " LANE ": " LN ",
        " PARKWAY ": " PKWY ", " SUITE ": " STE ", " APARTMENT ": " APT ",
        " FLOOR ": " FL ",
    }
    padded = f" {SPACE.sub(' ', text).strip()} "
    for source, target in replacements.items():
        padded = padded.replace(source, target)
    return SPACE.sub(" ", padded).strip()


def address_key(row: dict[str, str]) -> str:
    return "|".join(
        [
            normalize_address_part(row.get("owner_address_full")),
            normalize_address_part(row.get("owner_address_city_name")),
            normalize_address_part(row.get("owner_address_state")),
            re.sub(r"\D", "", clean(row.get("owner_address_zipcode_1")))[:5],
        ]
    )


def fetch(year: int, batch_size: int = 50000) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    offset = 0
    where = f"year={year} and upper(trim(owner_address_name)) like '%LLC'"
    while True:
        params = {
            "$select": ",".join(FIELDS),
            "$where": where,
            "$order": "pin",
            "$limit": str(batch_size),
            "$offset": str(offset),
        }
        url = API_URL + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=120) as response:
            batch = json.load(response)
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
        time.sleep(0.25)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()

    downloaded = fetch(args.year)
    parcels: list[dict[str, object]] = []
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)

    for raw in downloaded:
        owner_raw = clean(raw.get("owner_address_name"))
        owner_norm = normalize_name(owner_raw)
        key = address_key(raw)
        # The specification is a literal wildcard suffix rule (*LLC), so names
        # such as PLLC remain in scope when the normalized value ends in LLC.
        if not owner_norm.endswith("LLC") or not key.split("|", 1)[0]:
            continue
        row: dict[str, object] = {
            "market": "Chicago-Naperville-Elgin, IL-IN",
            "county": "Cook",
            "state": "IL",
            "tax_year": args.year,
            "parcel_id": clean(raw.get("pin")),
            "legal_owner_raw": owner_raw,
            "legal_owner_normalized": owner_norm,
            "owner_mailing_address_raw": clean(raw.get("owner_address_full")),
            "owner_mailing_city_raw": clean(raw.get("owner_address_city_name")),
            "owner_mailing_state_raw": clean(raw.get("owner_address_state")),
            "owner_mailing_zip_raw": clean(raw.get("owner_address_zipcode_1")),
            "owner_mailing_address_key": key,
            "property_address": clean(raw.get("prop_address_full")),
            "property_city": clean(raw.get("prop_address_city_name")),
            "property_state": clean(raw.get("prop_address_state")),
            "property_zip": clean(raw.get("prop_address_zipcode_1")),
            "source_dataset_id": DATASET_ID,
            "source_row_id": clean(raw.get("row_id")),
        }
        parcels.append(row)
        groups[key].append(row)

    clusters: list[dict[str, object]] = []
    for key, members in groups.items():
        llcs = sorted({str(m["legal_owner_normalized"]) for m in members})
        pins = sorted({str(m["parcel_id"]) for m in members})
        if len(llcs) < 2 or len(pins) < 2:
            continue
        first = members[0]
        clusters.append(
            {
                "owner_mailing_address_key": key,
                "mail_address": first["owner_mailing_address_raw"],
                "mail_city": first["owner_mailing_city_raw"],
                "mail_state": first["owner_mailing_state_raw"],
                "mail_zip": first["owner_mailing_zip_raw"],
                "distinct_llc_count": len(llcs),
                "property_count": len(pins),
                "llc_names": " | ".join(llcs),
                "parcel_ids": " | ".join(pins),
                "service_provider_review": "REQUIRED",
                "usps_cass_dpv_status": "NOT_RUN",
                "mailing_status": "RESEARCH_ONLY_NOT_MAIL_READY",
                "source_dataset_id": DATASET_ID,
                "source_tax_year": args.year,
            }
        )

    clusters.sort(key=lambda r: (-int(r["distinct_llc_count"]), -int(r["property_count"]), str(r["owner_mailing_address_key"])))
    parcels.sort(key=lambda r: (str(r["owner_mailing_address_key"]), str(r["legal_owner_normalized"]), str(r["parcel_id"])))

    processed = args.root / "03_PROCESSED"
    final = args.root / "01_FINAL_OUTPUTS"
    parcel_fields = list(parcels[0].keys()) if parcels else []
    cluster_fields = list(clusters[0].keys()) if clusters else []
    write_csv(processed / f"cook_{args.year}_llc_parcels.csv", parcels, parcel_fields)
    write_csv(processed / f"cook_{args.year}_address_clusters.csv", clusters, cluster_fields)
    write_csv(final / f"cook_{args.year}_candidate_mailing_addresses_RESEARCH_ONLY.csv", clusters, cluster_fields)

    print(json.dumps({
        "downloaded_rows": len(downloaded),
        "eligible_llc_parcels": len(parcels),
        "qualifying_address_clusters": len(clusters),
        "largest_cluster_llcs": clusters[0]["distinct_llc_count"] if clusters else 0,
        "mailing_ready": False,
    }, indent=2))


if __name__ == "__main__":
    main()
