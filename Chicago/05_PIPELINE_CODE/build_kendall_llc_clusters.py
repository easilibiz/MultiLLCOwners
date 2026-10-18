"""Download and cluster Kendall County LLC parcels by owner mailing address."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


SERVICE = "https://maps.co.kendall.il.us/server/rest/services/Hosted/Current_Cadastral_Features/FeatureServer/1"
FIELDS = ["pin", "parcel_type", "owner_name", "owner_addr1", "owner_addr2", "owner_csz", "site_address", "site_csz"]
SPACE = re.compile(r"\s+")
NON_ALNUM = re.compile(r"[^A-Z0-9#]+")
CSZ = re.compile(r"^(.*?)[, ]+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", re.I)


def clean(value: object) -> str:
    return SPACE.sub(" ", str(value or "").strip())


def normalize_name(value: object) -> str:
    return SPACE.sub(" ", re.sub(r"[,.]", "", clean(value).upper())).strip()


def normalize_address_part(value: object) -> str:
    text = NON_ALNUM.sub(" ", clean(value).upper())
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


def parse_csz(value: object) -> tuple[str, str, str]:
    raw = clean(value)
    match = CSZ.match(raw)
    if not match:
        return raw, "", ""
    return clean(match.group(1).rstrip(",")), match.group(2).upper(), match.group(3)


def fetch() -> list[dict[str, object]]:
    where = "upper(owner_name) like '%LLC'"
    ids_url = SERVICE + "/query?" + urllib.parse.urlencode({"where": where, "returnIdsOnly": "true", "f": "json"})
    with urllib.request.urlopen(ids_url, timeout=120) as response:
        payload = json.load(response)
    oid_field = payload["objectIdFieldName"]
    ids = sorted(payload.get("objectIds") or [])
    rows: list[dict[str, object]] = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        params = {
            "objectIds": ",".join(map(str, chunk)),
            "outFields": ",".join([oid_field, *FIELDS]),
            "returnGeometry": "false",
            "f": "json",
        }
        url = SERVICE + "/query?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=120) as response:
            data = json.load(response)
        rows.extend(feature["attributes"] for feature in data.get("features", []))
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot-date", default="2026-08-28")
    args = parser.parse_args()

    downloaded = fetch()
    parcels: list[dict[str, object]] = []
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for raw in downloaded:
        owner_raw = clean(raw.get("owner_name"))
        owner_norm = normalize_name(owner_raw)
        street = clean(" ".join(x for x in [clean(raw.get("owner_addr1")), clean(raw.get("owner_addr2"))] if x))
        city, state, postal = parse_csz(raw.get("owner_csz"))
        key = "|".join([
            normalize_address_part(street), normalize_address_part(city),
            normalize_address_part(state), re.sub(r"\D", "", postal)[:5],
        ])
        if not owner_norm.endswith("LLC") or not normalize_address_part(street):
            continue
        row: dict[str, object] = {
            "market": "Chicago-Naperville-Elgin, IL-IN",
            "county": "Kendall",
            "state": "IL",
            "source_snapshot_date": args.snapshot_date,
            "parcel_id": clean(raw.get("pin")),
            "legal_owner_raw": owner_raw,
            "legal_owner_normalized": owner_norm,
            "owner_mailing_address_raw": street,
            "owner_mailing_city_raw": city,
            "owner_mailing_state_raw": state,
            "owner_mailing_zip_raw": postal,
            "owner_mailing_address_key": key,
            "property_address": clean(raw.get("site_address")),
            "property_city_state_zip": clean(raw.get("site_csz")),
            "parcel_type": clean(raw.get("parcel_type")),
            "source_service": SERVICE,
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
        clusters.append({
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
            "source_snapshot_date": args.snapshot_date,
        })
    parcels.sort(key=lambda r: (str(r["owner_mailing_address_key"]), str(r["legal_owner_normalized"]), str(r["parcel_id"])))
    clusters.sort(key=lambda r: (-int(r["distinct_llc_count"]), -int(r["property_count"]), str(r["owner_mailing_address_key"])))

    stamp = args.snapshot_date.replace("-", "")
    write_csv(args.root / "03_PROCESSED" / f"kendall_{stamp}_llc_parcels.csv", parcels, list(parcels[0]) if parcels else [])
    write_csv(args.root / "03_PROCESSED" / f"kendall_{stamp}_address_clusters.csv", clusters, list(clusters[0]) if clusters else [])
    print(json.dumps({
        "downloaded_rows": len(downloaded),
        "eligible_llc_parcels": len(parcels),
        "qualifying_address_clusters": len(clusters),
        "mailing_ready": False,
    }, indent=2))


if __name__ == "__main__":
    main()
