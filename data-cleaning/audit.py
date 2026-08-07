#!/usr/bin/env python3
"""Independent audit of the documented dataset facts against the RAW CSV.

Shares no code with clean.py. Reads only briefing/ (read-only).
Prints PASS/FAIL per fact with observed numbers, then profiles for issues
NOT covered by the documented facts: null rates, negative values, outlier days,
structural breaks.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW_CSV = REPO / "briefing" / "Deel Marketing Analytics Challenge - Dataset - raw_data.csv"

results = []  # (fact, PASS/FAIL, observed)


def check(fact, ok, observed):
    results.append((fact, "PASS" if ok else "FAIL", observed))


def main():
    # --- raw header bytes, before any normalization ---
    raw_header = RAW_CSV.open(encoding="utf-8").readline().rstrip("\r\n")
    raw_cols = raw_header.split(",")
    nbsp_cols = [c for c in raw_cols if "\xa0" in c]
    check(
        "Headers contain \\xa0 in MQP and SQO columns",
        sorted(nbsp_cols) == sorted(["#\xa0Marketing Qualified Prospects",
                                     "#\xa0Sales Qualified Opportunities"]),
        f"\\xa0 found in: {[c.replace(chr(160), '<NBSP>') for c in nbsp_cols]}",
    )

    df = pd.read_csv(RAW_CSV, dtype=str, encoding="utf-8")
    df.columns = [re.sub(r"\s+", " ", c.replace("\xa0", " ")).strip() for c in df.columns]
    df = df.rename(columns={
        "Reporting Date": "date", "Marketing Team": "team", "Marketing Program": "program",
        "# Prospects": "prospects", "# Marketing Qualified Prospects": "mqp",
        "# Demo Prospects": "demo", "# Sales Qualified Opportunities": "sqo",
        "# Opportunities Won": "won", "$ Cost": "cost",
        "# Impressions": "impressions", "# Clicks": "clicks",
    })
    df["date"] = pd.to_datetime(df["date"])

    # --- $ Cost format ---
    has_dollar = df["cost"].str.contains(r"\$").all()
    has_thousands = df["cost"].str.contains(",").any()
    df["cost"] = pd.to_numeric(df["cost"].str.replace(r"[$,]", "", regex=True), errors="raise")
    check("$ Cost is a string with '$' and thousand separators, parseable to float",
          has_dollar and has_thousands,
          f"all values contain '$': {has_dollar}; some contain ',': {has_thousands}; all parsed OK")

    metrics = ["prospects", "mqp", "demo", "sqo", "won", "cost", "impressions", "clicks"]
    for c in [m for m in metrics if m != "cost"]:
        df[c] = pd.to_numeric(df[c], errors="raise")

    # --- date range / daily panel ---
    dmin, dmax = df["date"].min(), df["date"].max()
    all_days = pd.date_range("2023-07-01", "2025-06-30", freq="D")
    days_present = df["date"].nunique()
    check("Daily panel 2023-07-01 .. 2025-06-30 (two full Jul–Jun years)",
          dmin == all_days[0] and dmax == all_days[-1] and days_present == len(all_days),
          f"range {dmin.date()}..{dmax.date()}, {days_present}/{len(all_days)} calendar days present")

    # --- programs / teams ---
    n_prog, n_team = df["program"].nunique(), df["team"].nunique()
    teams = sorted(df["team"].unique())
    check("17 programs across 7 teams (paid, content, website, lifecycle, social, regional, event)",
          n_prog == 17 and n_team == 7
          and teams == sorted(["paid", "content", "website", "lifecycle", "social", "regional", "event"]),
          f"{n_prog} programs, {n_team} teams: {teams}")

    # --- duplicates ---
    dup_mask = df.duplicated(["date", "program"], keep=False)
    dup = df[dup_mask]
    n_dup_rows = len(dup)
    n_dup_keys = dup.groupby(["date", "program"]).ngroups
    dup_programs = sorted(dup["program"].unique()) if n_dup_rows else []
    in_late_june = ((dup["date"] >= "2025-06-01") & (dup["date"] <= "2025-06-30")).mean() if n_dup_rows else 0
    nz_rows_per_key = ((dup[metrics] != 0).any(axis=1)
                       .groupby([dup["date"], dup["program"]]).sum()) if n_dup_rows else pd.Series(dtype=int)
    one_real_one_zero = bool((nz_rows_per_key <= 1).all()) if n_dup_rows else True
    check("52 duplicate (date, program) rows in regional & website, late June 2025, one-real+one-zero",
          n_dup_rows == 52 and dup_programs == ["regional", "website"] and one_real_one_zero,
          f"{n_dup_rows} rows / {n_dup_keys} keys; programs {dup_programs}; "
          f"{in_late_june:.0%} of dup rows in June 2025; max non-zero rows per key = "
          f"{int(nz_rows_per_key.max()) if len(nz_rows_per_key) else 0}; "
          f"dates {sorted(d.date() for d in dup['date'].unique())[:5]}..")

    # --- clicks > impressions ---
    cgi = df[df["clicks"] > df["impressions"]]
    check("35 rows with clicks > impressions, in abm / paid_sponsorship / paid_awareness",
          len(cgi) == 35 and sorted(cgi["program"].unique()) == ["abm", "paid_awareness", "paid_sponsorship"],
          f"{len(cgi)} rows; programs {sorted(cgi['program'].unique())}")

    # --- fractional SQO / Won ---
    frac_sqo = int((df["sqo"] % 1 != 0).sum())
    frac_won = int((df["won"] % 1 != 0).sum())
    check("Decimal (fractional) values present in SQO and Won (MTA)",
          frac_sqo > 0 and frac_won > 0,
          f"{frac_sqo} rows with fractional SQO, {frac_won} with fractional Won")

    # --- stage-inversion rates (funnel lag) ---
    pct_mqp = (df["mqp"] > df["prospects"]).mean() * 100
    pct_demo = (df["demo"] > df["mqp"]).mean() * 100
    pct_won = (df["won"] > df["sqo"]).mean() * 100
    check("Stage inversions: MQP>Prospects ~13%, Demo>MQP ~29%, Won>SQO ~6% of rows",
          abs(pct_mqp - 13) <= 2 and abs(pct_demo - 29) <= 2 and abs(pct_won - 6) <= 2,
          f"MQP>Prospects {pct_mqp:.1f}%, Demo>MQP {pct_demo:.1f}%, Won>SQO {pct_won:.1f}%")

    # --- ooh / paid_other dead programs ---
    dead = df[df["program"].isin(["ooh", "paid_other"])]
    dead_total = dead[metrics].to_numpy().sum()
    check("ooh & paid_other: zero cost and zero outcomes across the period",
          len(dead) > 0 and dead_total == 0,
          f"{len(dead)} rows across ooh/paid_other; sum of all metrics = {dead_total}")

    # --- flighted programs ---
    flighted_obs = {}
    for prog in ["paid_awareness", "paid_sponsorship"]:
        p = df[df["program"] == prog]
        flighted_obs[prog] = {
            "days with cost>0": int((p["cost"] > 0).sum()),
            "days with any activity": int((p[metrics] != 0).any(axis=1).sum()),
            "days present": len(p),
        }
    active = [flighted_obs[p]["days with cost>0"] for p in flighted_obs]
    check("paid_awareness & paid_sponsorship flighted (~200–290 active days)",
          all(180 <= a <= 310 for a in active),
          "; ".join(f"{p}: {v}" for p, v in flighted_obs.items()))

    # --- impressions/clicks only in paid ---
    nonpaid_imp = df[(df["team"] != "paid") & ((df["impressions"] > 0) | (df["clicks"] > 0))]
    paid_with_imp = sorted(df[(df["team"] == "paid") & (df["impressions"] > 0)]["program"].unique())
    check("Only paid programs carry impressions/clicks",
          len(nonpaid_imp) == 0,
          f"non-paid rows with impressions/clicks: {len(nonpaid_imp)}"
          + (f" (programs: {sorted(nonpaid_imp['program'].unique())})" if len(nonpaid_imp) else "")
          + f"; paid programs with impressions: {paid_with_imp}")

    # ------------------------------------------------------------------
    print("=" * 100)
    print("AUDIT — documented dataset facts (ASSUMPTIONS.md) vs raw CSV")
    print("=" * 100)
    n_fail = 0
    for fact, verdict, observed in results:
        n_fail += verdict == "FAIL"
        print(f"[{verdict}] {fact}")
        print(f"       observed: {observed}")
    print(f"\n{len(results) - n_fail}/{len(results)} facts PASS, {n_fail} FAIL")

    # ------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("PROFILING — checks NOT covered by the documented facts")
    print("=" * 100)

    # Program -> team label consistency
    tpp = df.groupby("program")["team"].agg(lambda s: s.value_counts().to_dict())
    multi = {p: v for p, v in tpp.items() if len(v) > 1}
    print(f"\n0. Program->team label consistency: "
          + ("all programs map to exactly one team" if not multi
             else f"INCONSISTENT -> {multi}"))
    if multi:
        for p, v in multi.items():
            minority_team = min(v, key=v.get)
            mrows = df[(df["program"] == p) & (df["team"] == minority_team)]
            print(f"   {p}: minority team '{minority_team}' rows are all-zero: "
                  f"{bool((mrows[metrics] == 0).all().all())}; dates "
                  f"{mrows['date'].min().date()}..{mrows['date'].max().date()}")

    # Nulls
    nulls = df.isna().sum()
    print(f"1. Null values: total {int(nulls.sum())}"
          + ("" if nulls.sum() == 0 else f" -> {nulls[nulls > 0].to_dict()}"))

    # Negatives
    negs = {m: int((df[m] < 0).sum()) for m in metrics if (df[m] < 0).any()}
    print(f"2. Negative values: {negs if negs else 'none'}")

    # Per-program date coverage (gaps)
    print("3. Date coverage per program (days present of 731):")
    cov = df.groupby("program")["date"].agg(["nunique", "min", "max"])
    for prog, row in cov.sort_values("nunique").iterrows():
        gap = "" if row["nunique"] == 731 else f"  <-- {731 - row['nunique']} missing days"
        print(f"   {prog:35s} {row['nunique']:4d}  {row['min'].date()}..{row['max'].date()}{gap}")

    # Outlier days: value > 10x median of that program's non-zero days
    print("4. Outlier days (daily value > 10x program's non-zero median, min 30 non-zero days):")
    dd = df.groupby(["date", "program"], as_index=False)[metrics].sum()  # dup-safe view
    found = []
    for prog in sorted(df["program"].unique()):
        p = dd[dd["program"] == prog]
        for m in metrics:
            nz = p.loc[p[m] > 0, m]
            if len(nz) < 30:
                continue
            med = nz.median()
            out = p[p[m] > 10 * med]
            for _, r in out.iterrows():
                found.append((prog, m, r["date"].date(), r[m], med))
    if not found:
        print("   none")
    else:
        print(f"   {len(found)} program-metric-day outliers:")
        for prog, m, d, v, med in sorted(found, key=lambda x: -x[3] / x[4])[:15]:
            print(f"   {prog:28s} {m:12s} {d}  value={v:>12,.1f}  nonzero-median={med:,.1f}  ({v/med:.0f}x)")
        if len(found) > 15:
            print(f"   ... and {len(found) - 15} more (sorted by multiple of median)")

    # Structural breaks: monthly series, |mean after - mean before| > 3x pooled std
    print("5. Structural breaks (monthly level shifts > 3x pooled std, >= 4 months each side):")
    dd["ym"] = dd["date"].dt.to_period("M")
    breaks = []
    for prog in sorted(df["program"].unique()):
        p = dd[dd["program"] == prog]
        for m in metrics:
            s = p.groupby("ym")[m].sum()
            s = s[s.cumsum() > 0]  # drop leading all-zero months
            if len(s) < 8 or s.sum() == 0:
                continue
            best = None
            for k in range(4, len(s) - 3):
                a, b = s.iloc[:k], s.iloc[k:]
                pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
                if pooled == 0:
                    continue
                z = abs(b.mean() - a.mean()) / pooled
                if best is None or z > best[0]:
                    best = (z, s.index[k], a.mean(), b.mean())
            if best and best[0] > 3:
                breaks.append((prog, m, best))
    if not breaks:
        print("   none above threshold")
    else:
        for prog, m, (z, at, before, after) in sorted(breaks, key=lambda x: -x[2][0]):
            print(f"   {prog:28s} {m:12s} shift at {at}: monthly mean {before:,.0f} -> {after:,.0f} (z={z:.1f})")


if __name__ == "__main__":
    main()
