#!/usr/bin/env python3
"""Build a restartable NY DOS enrichment for the 3–6 LLC mailing population.

The script reads the completed ACRIS evidence in C:\\CodexCode\\NYCData,
selects either a 100-per-tier pilot or every High-confidence 3/4/5/6-LLC
address cluster, and matches their LLC names to NY Open Data dataset n9v6-gdp6.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


SOURCE_ROOT = Path(r"C:\CodexCode\NYCData")
CLUSTERS = SOURCE_ROOT / "data" / "output" / "probable_common_owner_clusters.csv"
EVIDENCE = SOURCE_ROOT / "data" / "output" / "ownership_evidence.csv"
ENV_FILE = SOURCE_ROOT / ".env"
DOS_ENDPOINT = "https://data.ny.gov/resource/n9v6-gdp6.json"
DOS_DATASET_PAGE = "https://data.ny.gov/Economic-Development/Active-Corporations-Beginning-1800/n9v6-gdp6"
DOS_SELECT = ",".join(
    [
        "dos_id",
        "current_entity_name",
        "initial_dos_filing_date",
        "county",
        "jurisdiction",
        "entity_type",
        "dos_process_name",
        "dos_process_address_1",
        "dos_process_address_2",
        "dos_process_city",
        "dos_process_state",
        "dos_process_zip",
        "chairman_name",
        "chairman_address_1",
        "chairman_address_2",
        "chairman_city",
        "chairman_state",
        "chairman_zip",
        "registered_agent_name",
        "registered_agent_address_1",
        "registered_agent_address_2",
        "registered_agent_city",
        "registered_agent_state",
        "registered_agent_zip",
        "location_name",
        "location_address_1",
        "location_address_2",
        "location_city",
        "location_state",
        "location_zip",
    ]
)

GENERIC_NAME_MARKERS = (
    "LIMITED LIABILITY COMPANY",
    "REGISTERED AGENT",
    "CORPORATION SERVICE",
    "CORPORATE SERVICE",
    "LEGALINC",
    "LEGALZOOM",
    "ZENBUSINESS",
    "NORTHWEST REGISTERED",
    "UNITED STATES CORPORATION AGENTS",
    "C T CORPORATION",
    "COGENCY",
    "SECRETARY OF STATE",
)


def normalize_text(value: object) -> str:
    text = str(value or "").upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_entity(value: object) -> str:
    text = normalize_text(value)
    text = re.sub(r"\b(LIMITED LIABILITY COMPANY|L L C)\b", "LLC", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_address(*parts: object) -> str:
    return normalize_text(" ".join(str(part or "") for part in parts))


def load_token() -> str:
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("NYC_OPEN_DATA_APP_TOKEN="):
            return line.split("=", 1)[1].strip()
    return ""


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split(" | ") if part.strip()]


def load_shortlist(
    limit_per_tier: int,
    all_eligible: bool = False,
    all_clusters: bool = False,
) -> list[dict[str, str]]:
    by_tier: dict[int, list[dict[str, str]]] = defaultdict(list)
    every_cluster: list[dict[str, str]] = []
    with CLUSTERS.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            every_cluster.append(row)
            count = int(row["distinct_llc_names"])
            if row["confidence"] == "High" and count in (3, 4, 5, 6):
                by_tier[count].append(row)

    if all_clusters:
        confidence_rank = {"High": 0, "Medium": 1, "Low": 2}
        rows = sorted(
            every_cluster,
            key=lambda r: (
                confidence_rank.get(r["confidence"], 9),
                -int(r["distinct_llc_names"]),
                -int(r["distinct_bbls"]),
                r["address_normalized"],
            ),
        )
        selected = []
        for index, row in enumerate(rows, 1):
            copied = dict(row)
            copied["cluster_id"] = f"DOS-ALL-{index:05d}"
            selected.append(copied)
        return selected

    selected: list[dict[str, str]] = []
    for tier in (3, 4, 5, 6):
        rows = sorted(
            by_tier[tier],
            key=lambda r: (
                -int(r["minimum_name_match"]),
                -int(r["distinct_bbls"]),
                -int(r["property_records"]),
                r["address_normalized"],
            ),
        )
        if not all_eligible:
            rows = rows[:limit_per_tier]
        if not all_eligible and len(rows) < limit_per_tier:
            raise RuntimeError(f"Only {len(rows)} eligible clusters found for {tier}-LLC tier")
        for index, row in enumerate(rows, 1):
            copied = dict(row)
            digits = 4 if all_eligible else 3
            copied["cluster_id"] = f"DOS-{tier}-{index:0{digits}d}"
            selected.append(copied)
    return selected


def raw_name_map(wanted_names: set[str]) -> dict[str, str]:
    choices: dict[str, Counter[str]] = defaultdict(Counter)
    with EVIDENCE.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            normalized = row["owner_normalized"].strip()
            if normalized in wanted_names:
                raw = row["assessment_owner"].strip()
                if raw:
                    choices[normalized][raw] += 1
    return {
        normalized: counts.most_common(1)[0][0]
        for normalized, counts in choices.items()
        if counts
    }


class DosClient:
    def __init__(self, token: str, requests_per_second: float = 3.0):
        self.headers = {"Accept": "application/json", "User-Agent": "NYC-LLC-DOS-Enrichment/1.0"}
        if token:
            self.headers["X-App-Token"] = token
        self.min_interval = 1.0 / max(requests_per_second, 0.1)
        self.last_request_started = 0.0
        self.rate_lock = threading.Lock()

    def get(self, params: dict[str, str], attempts: int = 5) -> list[dict[str, str]]:
        url = DOS_ENDPOINT + "?" + urllib.parse.urlencode(params)
        for attempt in range(attempts):
            with self.rate_lock:
                elapsed = time.monotonic() - self.last_request_started
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)
                self.last_request_started = time.monotonic()
            request = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == attempts - 1:
                    raise
            time.sleep(min(2 ** attempt, 15))
        return []

    def exact_batch(self, raw_names: list[str]) -> list[dict[str, str]]:
        quoted = ",".join("'" + name.upper().replace("'", "''") + "'" for name in raw_names)
        where = f"upper(current_entity_name) in({quoted})"
        return self.get({"$select": DOS_SELECT, "$where": where, "$limit": "5000"})

    def text_search(self, name: str) -> list[dict[str, str]]:
        return self.get({"$select": DOS_SELECT, "$q": name, "$limit": "50"})


def load_cache(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, list[dict[str, str]]]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def candidate_address(candidate: dict[str, str], prefix: str = "dos_process") -> str:
    return normalize_address(
        candidate.get(f"{prefix}_address_1"),
        candidate.get(f"{prefix}_address_2"),
        candidate.get(f"{prefix}_city"),
        candidate.get(f"{prefix}_state"),
        candidate.get(f"{prefix}_zip"),
    )


def address_match_score(candidate: dict[str, str], cluster_address: str) -> int:
    dos_address = candidate_address(candidate)
    deed_address = normalize_address(cluster_address)
    if dos_address and dos_address == deed_address:
        return 3
    street = normalize_text(candidate.get("dos_process_address_1"))
    zip_code = normalize_text(candidate.get("dos_process_zip"))[:5]
    if street and zip_code and street in deed_address and zip_code in deed_address:
        return 2
    if zip_code and zip_code in deed_address:
        return 1
    return 0


def best_candidate(candidates: list[dict[str, str]], cluster_address: str) -> tuple[dict[str, str] | None, int, int]:
    exact = [c for c in candidates if c.get("current_entity_name")]
    if not exact:
        return None, 0, 0
    ranked = sorted(
        exact,
        key=lambda c: (
            address_match_score(c, cluster_address),
            int("LIMITED LIABILITY" in c.get("entity_type", "").upper()),
            int(c.get("jurisdiction", "").upper() == "NEW YORK"),
            int(c.get("county", "").upper() in {"NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"}),
        ),
        reverse=True,
    )
    return ranked[0], len(exact), address_match_score(ranked[0], cluster_address)


def possible_person_name(value: str) -> bool:
    normalized = normalize_text(value)
    if not normalized or any(marker in normalized for marker in GENERIC_NAME_MARKERS):
        return False
    if re.search(r"\b(LLC|INC|CORP|COMPANY|CO|PLLC|LP|LTD|ASSOCIATES|REALTY)\b", normalized):
        return False
    words = normalized.split()
    return 2 <= len(words) <= 6 and all(not word.isdigit() for word in words)


def display_address(candidate: dict[str, str], prefix: str) -> str:
    return ", ".join(
        str(candidate.get(field, "")).strip()
        for field in (
            f"{prefix}_address_1",
            f"{prefix}_address_2",
            f"{prefix}_city",
            f"{prefix}_state",
            f"{prefix}_zip",
        )
        if str(candidate.get(field, "")).strip()
    )


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit-per-tier", type=int, default=100)
    parser.add_argument("--exact-batch-size", type=int, default=25)
    parser.add_argument("--use-cache-only", action="store_true")
    parser.add_argument("--all-eligible", action="store_true", help="Enrich every High-confidence 3–6 LLC group")
    parser.add_argument("--all-clusters", action="store_true", help="Enrich every candidate cluster, confidence level, and group size")
    parser.add_argument("--requests-per-second", type=float, default=3.0, help="Maximum DOS API request-start rate")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    shortlist = load_shortlist(args.limit_per_tier, args.all_eligible, args.all_clusters)
    wanted = {name for row in shortlist for name in split_pipe(row["llc_names"])}
    raw_names = raw_name_map(wanted)
    cache_path = args.output_dir / "dos_match_cache.json"
    cache = load_cache(cache_path)
    client = DosClient(load_token(), args.requests_per_second)

    pending = sorted(name for name in wanted if name not in cache)
    print(f"Selected {len(shortlist):,} mailing addresses and {len(wanted):,} unique LLC names")
    print(f"DOS cache: {len(cache):,} completed; {len(pending):,} pending", flush=True)

    # Fast exact-name pass, using the most common original assessment spelling.
    for start in range(0, 0 if args.use_cache_only else len(pending), args.exact_batch_size):
        batch = pending[start : start + args.exact_batch_size]
        query_names = [raw_names.get(name, name) for name in batch]
        rows = client.exact_batch(query_names)
        by_normalized: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_normalized[normalize_entity(row.get("current_entity_name"))].append(row)
        for name in batch:
            cache[name] = by_normalized.get(name, [])
        save_cache(cache_path, cache)
        completed = min(start + len(batch), len(pending))
        if completed % 100 == 0 or completed == len(pending):
            print(f"Exact DOS pass: {completed:,}/{len(pending):,}", flush=True)
        time.sleep(0.08)

    # Slower text-search pass catches punctuation and spacing differences.
    unmatched = [] if args.use_cache_only else sorted(name for name in wanted if not cache.get(name))
    print(f"Exact pass unmatched: {len(unmatched):,}; starting conservative fallback", flush=True)

    def fallback_search(name: str) -> tuple[str, list[dict[str, str]]]:
        search_rows = client.text_search(raw_names.get(name, name))
        matches = [
            row for row in search_rows if normalize_entity(row.get("current_entity_name")) == name
        ]
        return name, matches

    if unmatched:
        workers = max(2, min(8, int(args.requests_per_second * 2)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(fallback_search, name) for name in unmatched]
            for index, future in enumerate(as_completed(futures), 1):
                name, matches = future.result()
                cache[name] = matches
                if index % 10 == 0 or index == len(unmatched):
                    save_cache(cache_path, cache)
                if index % 25 == 0 or index == len(unmatched):
                    print(f"Fallback DOS pass: {index:,}/{len(unmatched):,}", flush=True)

    entity_rows: list[dict[str, object]] = []
    cluster_entities: dict[str, list[dict[str, object]]] = defaultdict(list)
    for cluster in shortlist:
        for normalized_name in split_pipe(cluster["llc_names"]):
            candidates = cache.get(normalized_name, [])
            chosen, candidate_count, addr_score = best_candidate(candidates, cluster["deed_party_address"])
            chosen = chosen or {}
            if not chosen:
                match_status = "No active DOS match"
            elif candidate_count > 1 and addr_score == 0:
                match_status = "Ambiguous active-name match"
            elif addr_score >= 2:
                match_status = "Address-corroborated active match"
            else:
                match_status = "Active name match"
            row: dict[str, object] = {
                "cluster_id": cluster["cluster_id"],
                "original_confidence": cluster["confidence"],
                "tier_llc_count": int(cluster["distinct_llc_names"]),
                "acris_shared_mailing_address": cluster["deed_party_address"],
                "llc_name_normalized": normalized_name,
                "assessment_name_used": raw_names.get(normalized_name, normalized_name),
                "match_status": match_status,
                "candidate_count": candidate_count,
                "address_match_score": addr_score,
                "dos_id": chosen.get("dos_id", ""),
                "current_entity_name": chosen.get("current_entity_name", ""),
                "initial_dos_filing_date": chosen.get("initial_dos_filing_date", ""),
                "county": chosen.get("county", ""),
                "jurisdiction": chosen.get("jurisdiction", ""),
                "entity_type": chosen.get("entity_type", ""),
                "dos_process_name": chosen.get("dos_process_name", ""),
                "dos_process_address": display_address(chosen, "dos_process"),
                "chairman_name": chosen.get("chairman_name", ""),
                "chairman_address": display_address(chosen, "chairman"),
                "registered_agent_name": chosen.get("registered_agent_name", ""),
                "registered_agent_address": display_address(chosen, "registered_agent"),
                "location_name": chosen.get("location_name", ""),
                "location_address": display_address(chosen, "location"),
                "email_from_dos": "",
                "phone_from_dos": "",
                "source_url": DOS_DATASET_PAGE,
            }
            entity_rows.append(row)
            cluster_entities[cluster["cluster_id"]].append(row)

    mailing_rows: list[dict[str, object]] = []
    for cluster in shortlist:
        entities = cluster_entities[cluster["cluster_id"]]
        matched = [row for row in entities if row["dos_id"]]
        address_corroborated = [row for row in matched if int(row["address_match_score"]) >= 2]
        dos_addresses = Counter(
            normalize_address(row["dos_process_address"])
            for row in matched
            if row["dos_process_address"]
        )
        shared_dos_count = max(dos_addresses.values(), default=0)
        shared_dos_normalized = dos_addresses.most_common(1)[0][0] if dos_addresses else ""
        shared_dos_display = next(
            (
                str(row["dos_process_address"])
                for row in matched
                if normalize_address(row["dos_process_address"]) == shared_dos_normalized
            ),
            "",
        )
        possible_names = Counter(
            str(row["dos_process_name"]).strip()
            for row in matched
            if possible_person_name(str(row["dos_process_name"]))
        )
        possible_addressee, addressee_count = possible_names.most_common(1)[0] if possible_names else ("", 0)
        recommended_addressee = possible_addressee if addressee_count >= 2 else "PROPERTY OWNER"
        if len(address_corroborated) >= 2:
            corroboration = "Strong DOS address corroboration"
        elif shared_dos_count >= 2:
            corroboration = "Shared DOS address"
        elif len(matched) >= max(2, len(entities) // 2):
            corroboration = "Active-name matches only"
        else:
            corroboration = "Needs manual review"
        raw_acris_address = split_pipe(cluster["deed_party_address"])[0]
        use_dos_address = shared_dos_count >= 2 and bool(address_corroborated)
        mailing_address = shared_dos_display if use_dos_address else raw_acris_address
        mailing_rows.append(
            {
                "cluster_id": cluster["cluster_id"],
                "original_confidence": cluster["confidence"],
                "mailing_tier": int(cluster["distinct_llc_names"]),
                "recommended_addressee": recommended_addressee,
                "possible_named_addressee": possible_addressee,
                "possible_addressee_support_count": addressee_count,
                "mailing_address": mailing_address,
                "mailing_address_source": "DOS address corroborated by ACRIS" if use_dos_address else "ACRIS deed-party address",
                "distinct_llcs": int(cluster["distinct_llc_names"]),
                "distinct_properties": int(cluster["distinct_bbls"]),
                "property_records": int(cluster["property_records"]),
                "llc_names": cluster["llc_names"],
                "property_addresses": cluster["property_addresses"],
                "dos_llcs_matched": len(matched),
                "dos_match_rate": len(matched) / len(entities) if entities else 0,
                "dos_address_corroborated_llcs": len(address_corroborated),
                "largest_shared_dos_address_count": shared_dos_count,
                "dos_corroboration": corroboration,
                "email_phone_available_from_dos": "No",
                "minimum_acris_name_match": int(cluster["minimum_name_match"]),
                "agent_address_marker": int(cluster["agent_address_marker"]),
                "situs_address_marker": int(cluster["situs_address_marker"]),
                "source_url": DOS_DATASET_PAGE,
            }
        )

    entity_fields = list(entity_rows[0].keys())
    mailing_fields = list(mailing_rows[0].keys())
    if args.all_clusters:
        entity_filename = "dos_entity_matches_all_clusters.csv"
        mailing_filename = "dos_mailing_shortlist_all_clusters.csv"
    elif args.all_eligible:
        entity_filename = "dos_entity_matches_all_3_to_6.csv"
        mailing_filename = "dos_mailing_shortlist_all_3_to_6.csv"
    else:
        entity_filename = "dos_entity_matches.csv"
        mailing_filename = "dos_mailing_shortlist_400.csv"
    write_csv(args.output_dir / entity_filename, entity_rows, entity_fields)
    write_csv(args.output_dir / mailing_filename, mailing_rows, mailing_fields)

    matched_entities = sum(bool(row["dos_id"]) for row in entity_rows)
    stats = {
        "mailing_addresses": len(mailing_rows),
        "unique_llc_names": len(wanted),
        "entity_rows": len(entity_rows),
        "matched_entity_rows": matched_entities,
        "match_rate": matched_entities / len(entity_rows) if entity_rows else 0,
        "address_corroborated_entity_rows": sum(int(row["address_match_score"]) >= 2 for row in entity_rows),
        "clusters_strong_dos_corroboration": sum(row["dos_corroboration"] == "Strong DOS address corroboration" for row in mailing_rows),
        "clusters_shared_dos_address": sum(row["dos_corroboration"] == "Shared DOS address" for row in mailing_rows),
        "clusters_with_possible_named_addressee": sum(row["recommended_addressee"] != "PROPERTY OWNER" for row in mailing_rows),
        "email_rows": 0,
        "phone_rows": 0,
        "scope": "all candidate clusters" if args.all_clusters else ("all High-confidence 3–6 LLC groups" if args.all_eligible else "400-address pilot"),
        "dataset_updated_note": "NY DOS dataset contains active entities only and is updated monthly.",
    }
    (args.output_dir / "dos_enrichment_stats.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )
    (args.output_dir / "workbook_data.json").write_text(
        json.dumps(
            {
                "stats": stats,
                "mailing_fields": mailing_fields,
                "mailing_rows": mailing_rows,
                "entity_fields": entity_fields,
                "entity_rows": entity_rows,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == "__main__":
    main()
