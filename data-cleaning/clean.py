#!/usr/bin/env python3
"""Cleaning pipeline: raw briefing CSV -> data-cleaning/output/clean_daily.csv.

Rules implemented (see ASSUMPTIONS.md):
- Header normalization (\xa0 -> space, collapse whitespace), rename to snake_case.
- $ Cost parsed to float (strip "$", thousand separators).
- (date, program) duplicates aggregated by sum, with a safety check: every
  duplicate key must have at most ONE non-zero row (one-real-plus-one-zero
  pattern). If any key has >= 2 non-zero rows the script STOPS with exit 1.
- No row deletions: clicks > impressions rows get a boolean flag;
  ooh / paid_other get an excluded flag with reason.
- Helper columns: fiscal_year (Jul-Jun, raises on out-of-range dates),
  year_month, is_paid.
- Post-clean assertions: unique (date, program) keys; all metrics >= 0.
- Deterministic sort + fixed column order -> idempotent output.
"""

import io
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW_CSV = REPO / "briefing" / "Deel Marketing Analytics Challenge - Dataset - raw_data.csv"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_CSV = OUT_DIR / "clean_daily.csv"
OUT_REPORT = OUT_DIR / "cleaning_report.txt"

RENAME = {
    "Reporting Date": "date",
    "Marketing Team": "team",
    "Marketing Program": "program",
    "# Prospects": "prospects",
    "# Marketing Qualified Prospects": "mqp",
    "# Demo Prospects": "demo",
    "# Sales Qualified Opportunities": "sqo",
    "# Opportunities Won": "won",
    "$ Cost": "cost",
    "# Impressions": "impressions",
    "# Clicks": "clicks",
}

METRICS = ["prospects", "mqp", "demo", "sqo", "won", "cost", "impressions", "clicks"]
INT_METRICS = ["prospects", "mqp", "demo", "impressions", "clicks"]
FLOAT_METRICS = ["sqo", "won", "cost"]  # sqo/won fractional by design (MTA)

EXCLUDED_PROGRAMS = {
    "ooh": "zero cost and zero outcomes across full period",
    "paid_other": "zero cost and zero outcomes across full period",
}

FY_START, FY_END = pd.Timestamp("2023-07-01"), pd.Timestamp("2025-06-30")

report_lines = []


def log(msg=""):
    print(msg)
    report_lines.append(msg)


def normalize_header(h):
    return re.sub(r"\s+", " ", h.replace("\xa0", " ")).strip()


def parse_cost(s):
    cleaned = s.str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.strip()
    bad = ~cleaned.str.fullmatch(r"-?\d+(\.\d+)?")
    if bad.any():
        raise ValueError(f"Unparseable $ Cost values: {s[bad].unique()[:10]}")
    return cleaned.astype(float)


def fiscal_year(dates):
    out_of_range = (dates < FY_START) | (dates > FY_END)
    if out_of_range.any():
        raise ValueError(
            f"{out_of_range.sum()} dates outside {FY_START.date()}..{FY_END.date()}: "
            f"{sorted(dates[out_of_range].dt.date.unique())[:10]}"
        )
    return dates.apply(lambda d: "FY24" if d < pd.Timestamp("2024-07-01") else "FY25")


def main():
    log("=" * 70)
    log("CLEANING REPORT — clean.py")
    log("=" * 70)

    raw = pd.read_csv(RAW_CSV, dtype=str, encoding="utf-8")
    n_in = len(raw)
    log(f"Rows in (raw):  {n_in}")

    # 1. Header normalization
    orig_cols = list(raw.columns)
    raw.columns = [normalize_header(c) for c in raw.columns]
    n_headers_changed = sum(o != n for o, n in zip(orig_cols, raw.columns))
    log(f"Headers normalized (\\xa0 / whitespace): {n_headers_changed} of {len(orig_cols)}")
    missing = set(RENAME) - set(raw.columns)
    if missing:
        raise ValueError(f"Expected columns missing after normalization: {missing}")
    df = raw.rename(columns=RENAME)[list(RENAME.values())]

    # 2. Type parsing
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")  # raises on bad dates
    df["cost"] = parse_cost(df["cost"])
    for c in [m for m in METRICS if m != "cost"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    log(f"$ Cost values parsed to float: {n_in}")

    # 3. Team-per-program consistency (required for sum-dedup keyed on (date, program)).
    # Known raw-data defect: the all-zero duplicate rows for regional/website carry a
    # wrong team label ('lifecycle'). Resolve team to the program's majority value,
    # but only if every minority-team row is an all-zero duplicate row — else stop.
    teams_per_program = df.groupby("program")["team"].nunique()
    multi = teams_per_program[teams_per_program > 1]
    if len(multi):
        log(f"\nPrograms with >1 team value in raw data: {list(multi.index)}")
        dup_key_mask = df.duplicated(subset=["date", "program"], keep=False)
        for prog in multi.index:
            sub = df[df["program"] == prog]
            counts = sub["team"].value_counts()
            majority = counts.idxmax()
            minority_rows = sub[sub["team"] != majority]
            all_zero = (minority_rows[METRICS] == 0).all(axis=1).all()
            all_dup = dup_key_mask[minority_rows.index].all()
            log(f"  {prog}: {counts.to_dict()} -> canonical team '{majority}' "
                f"(minority rows all-zero: {all_zero}, all duplicate keys: {all_dup})")
            if not (all_zero and all_dup):
                log(f"STOP: minority-team rows for '{prog}' are not all-zero duplicates — review.")
                OUT_DIR.mkdir(exist_ok=True)
                OUT_REPORT.write_text("\n".join(report_lines) + "\n")
                sys.exit(1)
        canonical = df.groupby("program")["team"].agg(lambda s: s.value_counts().idxmax())
        df["team"] = df["program"].map(canonical)

    # 4. Dedup by (date, program) with sum + safety check
    dup_mask = df.duplicated(subset=["date", "program"], keep=False)
    dup_rows = df[dup_mask]
    n_dup_keys = dup_rows.groupby(["date", "program"]).ngroups
    log(f"\nDuplicate (date, program) keys: {n_dup_keys} ({len(dup_rows)} rows involved)")
    if n_dup_keys:
        log(f"  Programs affected: {sorted(dup_rows['program'].unique())}")
        log(f"  Date range of duplicates: {dup_rows['date'].min().date()} .. {dup_rows['date'].max().date()}")
        nonzero_row = (dup_rows[METRICS] != 0).any(axis=1)
        nz_per_key = nonzero_row.groupby([dup_rows["date"], dup_rows["program"]]).sum()
        log("  Non-zero rows per duplicate key (safety check):")
        for count, keys in nz_per_key.value_counts().sort_index().items():
            log(f"    {keys} keys with {count} non-zero row(s)")
        offenders = nz_per_key[nz_per_key >= 2]
        if len(offenders):
            log("\nSTOP: duplicate keys with >= 2 non-zero rows — sum-aggregation not")
            log("validated for these keys. Review before proceeding:")
            for (d, p), k in offenders.items():
                log(f"  {d.date()} {p}: {k} non-zero rows")
            OUT_DIR.mkdir(exist_ok=True)
            OUT_REPORT.write_text("\n".join(report_lines) + "\n")
            sys.exit(1)

    agg = {m: "sum" for m in METRICS}
    agg["team"] = "first"
    df = df.groupby(["date", "program"], as_index=False).agg(agg)
    n_collapsed = n_in - len(df)
    log(f"  Rows collapsed by sum-aggregation: {n_collapsed}")

    # 5. Flags (no deletions)
    df["flag_clicks_gt_impressions"] = df["clicks"] > df["impressions"]
    n_ctr_flag = int(df["flag_clicks_gt_impressions"].sum())
    log(f"\nFlagged clicks > impressions: {n_ctr_flag} rows "
        f"(programs: {sorted(df.loc[df['flag_clicks_gt_impressions'], 'program'].unique())})")

    for prog, reason in EXCLUDED_PROGRAMS.items():
        prog_rows = df[df["program"] == prog]
        if prog_rows[METRICS].to_numpy().sum() != 0:
            raise ValueError(f"'{prog}' has non-zero activity; exclusion reason invalid — review.")
    df["flag_excluded"] = df["program"].isin(EXCLUDED_PROGRAMS)
    df["exclude_reason"] = df["program"].map(EXCLUDED_PROGRAMS).fillna("")
    n_excl = int(df["flag_excluded"].sum())
    log(f"Flagged excluded (ooh, paid_other — zero cost & outcomes): {n_excl} rows")

    # 6. Helper columns
    df["fiscal_year"] = fiscal_year(df["date"])
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["is_paid"] = df["team"] == "paid"

    # 7. Post-clean assertions
    assert len(df) == df.groupby(["date", "program"]).ngroups, "duplicate keys remain"
    for m in METRICS:
        assert (df[m] >= 0).all(), f"negative values in {m}"
    for m in INT_METRICS:
        assert (df[m] == df[m].astype(int)).all(), f"non-integer values in {m}"
        df[m] = df[m].astype(int)
    log("\nAssertions passed: unique (date, program) keys; all metrics >= 0; "
        "prospects/mqp/demo/impressions/clicks integral.")

    # 8. Deterministic output
    df = df.sort_values(["date", "program"]).reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    cols = ["date", "team", "program", "prospects", "mqp", "demo", "sqo", "won",
            "cost", "impressions", "clicks", "fiscal_year", "year_month", "is_paid",
            "flag_clicks_gt_impressions", "flag_excluded", "exclude_reason"]
    df = df[cols]

    OUT_DIR.mkdir(exist_ok=True)
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n")
    OUT_CSV.write_text(buf.getvalue())

    log(f"\nRows out (clean): {len(df)}")
    log(f"Programs: {df['program'].nunique()}  Teams: {df['team'].nunique()}")
    log(f"Date coverage: {df['date'].min()} .. {df['date'].max()}")
    log(f"Fiscal years: {df.groupby('fiscal_year').size().to_dict()}")
    log(f"\nWrote {OUT_CSV.relative_to(REPO)}")
    OUT_REPORT.write_text("\n".join(report_lines) + "\n")
    log(f"Wrote {OUT_REPORT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
