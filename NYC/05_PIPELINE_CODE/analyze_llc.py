import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fy2027_final_llc_properties.csv"
OUT = ROOT / "processed"


def normalize_owner(value: object) -> str:
    text = "" if pd.isna(value) else str(value).upper().strip()
    text = text.replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\bL\s+L\s+C\b", "LLC", text)
    text = re.sub(r"\bLIMITED\s+LIABILITY\s+(?:COMPANY|CO)\b", "LLC", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    dtype = {
        "parid": "string",
        "boro": "Int64",
        "block": "Int64",
        "lot": "Int64",
        "year": "string",
        "period": "string",
        "owner": "string",
        "bldg_class": "string",
        "fintaxclass": "string",
        "housenum_lo": "string",
        "housenum_hi": "string",
        "street_name": "string",
        "aptno": "string",
        "zip_code": "string",
        "units": "Float64",
        "finmkttot": "Float64",
        "finacttot": "Float64",
    }
    df = pd.read_csv(SOURCE, dtype=dtype)
    source_rows = len(df)
    df = df.drop_duplicates().copy()
    df["owner_normalized"] = df["owner"].map(normalize_owner)

    house_lo = clean_text(df["housenum_lo"])
    house_hi = clean_text(df["housenum_hi"])
    house = house_lo.where((house_hi == "") | (house_hi == house_lo), house_lo + "-" + house_hi)
    street = clean_text(df["street_name"]).str.upper()
    apt = clean_text(df["aptno"]).str.upper()
    zipcode = clean_text(df["zip_code"])
    zipcode = zipcode.mask(zipcode.isin(["0", "00000"]), "")
    df["property_address"] = (house + " " + street).str.replace(r"\s+", " ", regex=True).str.strip()
    df.loc[apt != "", "property_address"] += " APT " + apt[apt != ""]
    df.loc[zipcode != "", "property_address"] += ", NY " + zipcode[zipcode != ""]
    df["bbl"] = (
        df["boro"].astype("string").str.zfill(1)
        + df["block"].astype("string").str.zfill(5)
        + df["lot"].astype("string").str.zfill(4)
    )
    df["borough"] = df["boro"].map(
        {1: "Manhattan", 2: "Bronx", 3: "Brooklyn", 4: "Queens", 5: "Staten Island"}
    )

    clean_cols = [
        "parid", "bbl", "borough", "block", "lot", "owner", "owner_normalized",
        "property_address", "bldg_class", "fintaxclass", "units", "finmkttot", "finacttot",
    ]
    clean = df[clean_cols].sort_values(["owner_normalized", "borough", "block", "lot"])
    clean.to_csv(OUT / "fy2027_final_llc_properties_clean.csv", index=False)

    grouped = (
        clean.groupby("owner_normalized", dropna=False)
        .agg(
            owner_as_listed=("owner", "first"),
            property_records=("parid", "nunique"),
            tax_lots=("bbl", "nunique"),
            borough_count=("borough", "nunique"),
            boroughs=("borough", lambda s: ", ".join(sorted(set(s.dropna())))),
            total_units=("units", "sum"),
            total_market_value=("finmkttot", "sum"),
            total_assessed_value=("finacttot", "sum"),
        )
        .reset_index()
    )
    grouped["multiple_properties"] = grouped["property_records"] > 1
    grouped = grouped.sort_values(
        ["property_records", "total_market_value", "owner_normalized"],
        ascending=[False, False, True],
    )
    grouped.to_csv(OUT / "llc_owner_summary_all.csv", index=False)
    grouped[grouped["multiple_properties"]].to_csv(
        OUT / "llc_multi_property_summary.csv", index=False
    )

    valid_address_mask = (
        (house_lo.str.len() > 0)
        & (house_lo != "0")
        & (street.str.len() > 0)
        & (zipcode.str.len() >= 5)
    )
    valid_parids = set(df.loc[valid_address_mask, "parid"].dropna())
    valid_addresses = clean[clean["parid"].isin(valid_parids)].copy()
    address_groups = (
        valid_addresses.groupby("property_address")
        .agg(
            distinct_llc_names=("owner_normalized", "nunique"),
            property_records=("parid", "nunique"),
            llc_names=("owner_normalized", lambda s: " | ".join(sorted(set(s)))),
            boroughs=("borough", lambda s: ", ".join(sorted(set(s.dropna())))),
            total_market_value=("finmkttot", "sum"),
        )
        .reset_index()
    )
    address_groups = address_groups[address_groups["distinct_llc_names"] > 1]
    address_groups = address_groups.sort_values(
        ["distinct_llc_names", "property_records", "total_market_value"],
        ascending=[False, False, False],
    )
    address_groups.to_csv(OUT / "shared_property_address_candidates.csv", index=False)

    metrics = pd.DataFrame(
        [
            ["Downloaded final-roll rows", source_rows],
            ["Unique final-roll property records", clean["parid"].nunique()],
            ["Distinct normalized LLC names", grouped["owner_normalized"].nunique()],
            ["LLC names with multiple property records", int(grouped["multiple_properties"].sum())],
            ["Properties held by multi-property LLC names", int(clean[clean["owner_normalized"].isin(grouped.loc[grouped["multiple_properties"], "owner_normalized"])]["parid"].nunique())],
            ["Property addresses listing multiple LLC names", len(address_groups)],
        ],
        columns=["metric", "value"],
    )
    metrics.to_csv(OUT / "metrics.csv", index=False)
    workbook_data = {}
    for key, frame in {
        "metrics": metrics,
        "multi_property": grouped[grouped["multiple_properties"]],
        "shared_property_addresses": address_groups,
    }.items():
        safe = frame.astype(object).where(pd.notna(frame), None)
        workbook_data[key] = {
            "columns": list(safe.columns),
            "data": safe.values.tolist(),
        }
    with (OUT / "workbook_data.json").open("w", encoding="utf-8") as handle:
        json.dump(workbook_data, handle, ensure_ascii=False)
    print(metrics.to_string(index=False))
    print(f"Multi-property LLC groups: {int(grouped['multiple_properties'].sum()):,}")
    print(f"Shared property-address groups: {len(address_groups):,}")


if __name__ == "__main__":
    main()
