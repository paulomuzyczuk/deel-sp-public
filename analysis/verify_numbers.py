#!/usr/bin/env python3
"""Independent re-derivation of every Task 1 headline number from the RAW CSV.

Shares no code with clean.py or the notebook: does its own minimal cleaning
(header normalization, cost parse, (date, program) sum-dedup, exclusions) and
recomputes each number cited in the notebook's 1.4/1.5 sections, printing
PASS/FAIL against the cited values. Exit code 1 on any FAIL.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "briefing" / "Deel Marketing Analytics Challenge - Dataset - raw_data.csv"

results = []


def check(name, observed, expected, tol=0.01):
    ok = abs(observed - expected) <= tol * max(1.0, abs(expected))
    results.append((name, ok, observed, expected))


def main():
    df = pd.read_csv(RAW, dtype=str, encoding="utf-8")
    df.columns = [re.sub(r"\s+", " ", c.replace("\xa0", " ")).strip() for c in df.columns]
    df = df.rename(columns={
        "Reporting Date": "date", "Marketing Team": "team", "Marketing Program": "program",
        "# Prospects": "prospects", "# Marketing Qualified Prospects": "mqp",
        "# Demo Prospects": "demo", "# Sales Qualified Opportunities": "sqo",
        "# Opportunities Won": "won", "$ Cost": "cost",
        "# Impressions": "impressions", "# Clicks": "clicks"})
    df["date"] = pd.to_datetime(df["date"])
    df["cost"] = pd.to_numeric(df["cost"].str.replace(r"[$,]", "", regex=True))
    metrics = ["prospects", "mqp", "demo", "sqo", "won", "cost", "impressions", "clicks"]
    for m in [x for x in metrics if x != "cost"]:
        df[m] = pd.to_numeric(df[m])

    # dedup by (date, program) sum; team = majority label per program
    team_map = df.groupby("program")["team"].agg(lambda s: s.value_counts().idxmax())
    d = df.groupby(["date", "program"], as_index=False)[metrics].sum()
    d["team"] = d["program"].map(team_map)
    d = d[~d["program"].isin(["ooh", "paid_other"])]                    # exclusions
    d["fy"] = np.where(d["date"] < "2024-07-01", "FY24", "FY25")
    d["ym"] = d["date"].dt.to_period("M")

    # ---- FY totals & YoY ----
    paid = d[d["team"] == "paid"]
    fy_b = d.groupby("fy")[["prospects", "demo", "sqo", "won"]].sum()
    fy_t = paid.groupby("fy")[["impressions", "clicks"]].sum()
    yoy = lambda t, m: (t.loc["FY25", m] / t.loc["FY24", m] - 1) * 100
    check("impressions YoY % (paid)", yoy(fy_t, "impressions"), 3.6, 0.02)
    check("clicks YoY % (paid)", yoy(fy_t, "clicks"), -1.5, 0.02)
    check("prospects YoY %", yoy(fy_b, "prospects"), 52.6, 0.002)
    check("demo YoY %", yoy(fy_b, "demo"), 9.8, 0.005)
    check("SQO FY24 total", fy_b.loc["FY24", "sqo"], 19323.4, 0.0001)
    check("SQO FY25 total", fy_b.loc["FY25", "sqo"], 26178.1, 0.0001)
    check("SQO YoY %", yoy(fy_b, "sqo"), 35.5, 0.002)
    check("Won FY24 total", fy_b.loc["FY24", "won"], 4156.2, 0.0001)
    check("Won FY25 total", fy_b.loc["FY25", "won"], 7118.5, 0.0001)
    check("Won YoY %", yoy(fy_b, "won"), 71.3, 0.002)

    # ---- team shares ----
    share = d.groupby("team")[["prospects", "sqo", "won"]].sum()
    share = share / share.sum() * 100
    check("paid share of SQO %", share.loc["paid", "sqo"], 81.9, 0.002)
    check("paid share of Won %", share.loc["paid", "won"], 79.3, 0.002)
    check("event share of prospects %", share.loc["event", "prospects"], 31.4, 0.002)
    check("event share of SQO %", share.loc["event", "sqo"], 2.9, 0.02)

    # ---- MQP tracking artifact ----
    check("MQP total before 2024-01-03", d.loc[d["date"] < "2024-01-03", "mqp"].sum(), 0, 0)

    # ---- channel FY rates (CTR excludes clicks>impressions rows; none in these channels) ----
    ch = d[d["program"].isin(["paid_search", "paid_brand_search", "paid_social"])]
    ch = ch[~(ch["clicks"] > ch["impressions"])]
    g = ch.groupby(["program", "fy"])[["impressions", "clicks", "demo", "sqo", "cost"]].sum()
    val = lambda p, f, m: g.loc[(p, f), m]
    check("brand_search FY25 CTR %", val("paid_brand_search", "FY25", "clicks") / val("paid_brand_search", "FY25", "impressions") * 100, 8.85, 0.005)
    check("paid_search FY25 CTR %", val("paid_search", "FY25", "clicks") / val("paid_search", "FY25", "impressions") * 100, 2.79, 0.005)
    check("paid_search FY24 CTR %", val("paid_search", "FY24", "clicks") / val("paid_search", "FY24", "impressions") * 100, 5.54, 0.005)
    check("paid_social FY25 CTR %", val("paid_social", "FY25", "clicks") / val("paid_social", "FY25", "impressions") * 100, 0.37, 0.02)
    check("brand_search FY25 demo->SQO %", val("paid_brand_search", "FY25", "sqo") / val("paid_brand_search", "FY25", "demo") * 100, 57.35, 0.005)
    check("paid_search FY25 demo->SQO %", val("paid_search", "FY25", "sqo") / val("paid_search", "FY25", "demo") * 100, 38.92, 0.005)
    check("paid_social FY25 demo->SQO %", val("paid_social", "FY25", "sqo") / val("paid_social", "FY25", "demo") * 100, 34.49, 0.005)
    check("brand_search FY24 cost/SQO $", val("paid_brand_search", "FY24", "cost") / val("paid_brand_search", "FY24", "sqo"), 3286, 0.005)
    check("brand_search FY25 cost/SQO $", val("paid_brand_search", "FY25", "cost") / val("paid_brand_search", "FY25", "sqo"), 7213, 0.005)
    check("paid_search FY25 cost/SQO $", val("paid_search", "FY25", "cost") / val("paid_search", "FY25", "sqo"), 10609, 0.005)
    check("paid_social FY25 cost/SQO $", val("paid_social", "FY25", "cost") / val("paid_social", "FY25", "sqo"), 26826, 0.005)
    check("brand_search FY25 SQO/1k clicks", val("paid_brand_search", "FY25", "sqo") / val("paid_brand_search", "FY25", "clicks") * 1000, 4.2, 0.02)
    check("brand_search spend FY24 $M", val("paid_brand_search", "FY24", "cost") / 1e6, 23.7, 0.005)
    check("brand_search spend FY25 $M", val("paid_brand_search", "FY25", "cost") / 1e6, 69.1, 0.005)
    check("paid_search impressions YoY %", (val("paid_search", "FY25", "impressions") / val("paid_search", "FY24", "impressions") - 1) * 100, 124, 0.02)

    # ---- seasonality (centered 12-mo rolling mean, min 6 of 13; same defs as notebook) ----
    def dev(metric):
        s = d.groupby("ym")[metric].sum().sort_index()
        r = s.rolling(13, center=True, min_periods=6).mean()
        return (s / r - 1) * 100

    sq = dev("sqo")
    check("SQO Dec-23 deviation %", sq.loc[pd.Period("2023-12")], -43.7, 0.02)
    check("SQO Dec-24 deviation %", sq.loc[pd.Period("2024-12")], -10.6, 0.03)
    dm = dev("demo")
    check("demo Oct-23 deviation %", dm.loc[pd.Period("2023-10")], 18, 0.06)
    check("demo Oct-24 deviation %", dm.loc[pd.Period("2024-10")], 18, 0.06)

    # ---- fig2 title counts ----
    mm = d.groupby("ym")[["sqo", "won"]].sum()
    mm.index = mm.index.to_timestamp()
    fm = [(i.month - 7) % 12 for i in mm.index]
    t = mm.assign(fy=np.where(mm.index < "2024-07-01", "FY24", "FY25"), fm=fm)
    for m, exp in [("sqo", 10), ("won", 11)]:
        p = t.pivot_table(index="fm", columns="fy", values=m)
        check(f"months FY25>FY24 ({m})", int((p["FY25"] > p["FY24"]).sum()), exp, 0)

    # ---- weekend share ----
    daily = d.groupby("date")[["demo", "sqo", "won"]].sum()
    dw = daily.groupby(daily.index.dayofweek).mean()
    wknd = dw.loc[[5, 6]].mean() / dw.loc[[0, 1, 2, 3, 4]].mean() * 100
    check("weekend demo % of weekday", wknd["demo"], 3.5, 0.06)
    check("weekend SQO % of weekday", wknd["sqo"], 6.5, 0.06)
    check("weekend Won % of weekday", wknd["won"], 9.2, 0.06)

    # ================= Task 2 headline numbers =================
    # Rider A: SQO->Won decomposition
    tot = d.groupby("fy")[["sqo", "won"]].sum()
    q24 = tot.loc["FY24", "won"] / tot.loc["FY24", "sqo"] * 100
    q25 = tot.loc["FY25", "won"] / tot.loc["FY25", "sqo"] * 100
    check("SQO->Won FY24 %", q24, 21.5, 0.005)
    check("SQO->Won FY25 %", q25, 27.2, 0.005)
    check("SQO->Won rate factor", q25 / q24, 1.264, 0.002)

    fyp = d.groupby(["program", "fy"])[["sqo", "won"]].sum().unstack()
    fyp.columns = [f"{a}_{b}" for a, b in fyp.columns]
    big = fyp[(fyp.sqo_FY24 >= 100) & (fyp.sqo_FY25 >= 100)]
    delta = big.won_FY25 / big.sqo_FY25 * 100 - big.won_FY24 / big.sqo_FY24 * 100
    check("programs >=100 SQO both FYs", len(big), 10, 0)
    check("programs improved (of 10)", int((delta > 0).sum()), 8, 0)
    check("brand_search SQO->Won delta pp", delta["paid_brand_search"], 10.1, 0.005)

    g2 = fyp[fyp.sqo_FY24 > 0]
    s25 = g2.sqo_FY25 / g2.sqo_FY25.sum()
    s24 = g2.sqo_FY24 / g2.sqo_FY24.sum()
    p24_, p25_ = g2.won_FY24 / g2.sqo_FY24, g2.won_FY25 / g2.sqo_FY25
    check("within-program effect pp", float((s25 * (p25_ - p24_)).sum() * 100), 5.0, 0.02)
    check("mix effect pp", float(((s25 - s24) * p24_).sum() * 100), 0.7, 0.06)
    check("brand_search within contribution pp", float((s25 * (p25_ - p24_))["paid_brand_search"] * 100), 3.7, 0.02)
    dw = g2.won_FY25 - g2.won_FY24
    check("brand+search share of incr. Won %",
          float(((dw / dw.sum() * 100)[["paid_brand_search", "paid_search"]]).sum()), 81.3, 0.005)

    # 2.1/2.2 unit costs (cost per attributed stage, FY sums)
    fc = d.groupby(["program", "fy"])[["cost", "impressions", "sqo", "won"]].sum()
    ups = lambda p, f, m: fc.loc[(p, f), "cost"] / fc.loc[(p, f), m]
    check("search FY24 cost/SQO $", ups("paid_search", "FY24", "sqo"), 8801, 0.005)
    check("search FY25 cost/won $", ups("paid_search", "FY25", "won"), 46801, 0.005)
    check("social FY24 cost/SQO $", ups("paid_social", "FY24", "sqo"), 35744, 0.005)
    check("social FY24 cost/won $", ups("paid_social", "FY24", "won"), 328819, 0.005)
    check("social FY25 cost/won $", ups("paid_social", "FY25", "won"), 138618, 0.005)
    check("brand FY25 cost/won $", ups("paid_brand_search", "FY25", "won"), 21250, 0.005)
    check("listicle FY24 cost/SQO $", ups("listicle_leadbuy_listing", "FY24", "sqo"), 7601, 0.005)
    check("listicle FY25 cost/SQO $", ups("listicle_leadbuy_listing", "FY25", "sqo"), 6833, 0.005)
    check("listicle FY25 cost/won $", ups("listicle_leadbuy_listing", "FY25", "won"), 40052, 0.005)

    # paid_search Oct-24 step-up before/after
    pm = d[d["program"] == "paid_search"].groupby("ym")[["cost", "impressions", "sqo"]].sum()
    b, a = pm.loc[pd.Period("2023-10"):pd.Period("2024-09")], pm.loc[pd.Period("2024-10"):pd.Period("2025-06")]
    check("step-up: before cost/SQO $", b.cost.sum() / b.sqo.sum(), 7878, 0.005)
    check("step-up: after cost/SQO $", a.cost.sum() / a.sqo.sum(), 12061, 0.005)
    check("step-up: impressions ratio", a.impressions.mean() / b.impressions.mean(), 2.56, 0.005)
    check("step-up: cost ratio", a.cost.mean() / b.cost.mean(), 1.86, 0.005)
    check("step-up: SQO ratio", a.sqo.mean() / b.sqo.mean(), 1.21, 0.005)
    check("step-up: marginal cost/SQO $", (a.cost.mean() - b.cost.mean()) / (a.sqo.mean() - b.sqo.mean()), 31734, 0.005)

    # 2.3 / 2.5
    lc = d[d["team"] == "lifecycle"].groupby("fy")["sqo"].sum()
    check("lifecycle SQO YoY %", (lc["FY25"] / lc["FY24"] - 1) * 100, 114.4, 0.005)
    zc = ["content", "website", "social", "lifecycle"]
    check("zero-cost teams total cost", d.loc[d["team"].isin(zc), "cost"].sum(), 0, 0)
    f25 = d[d["fy"] == "FY25"]
    check("zero-cost share of FY25 SQO %", f25[f25["team"].isin(zc)].sqo.sum() / f25.sqo.sum() * 100, 13.6, 0.01)
    tc = d.groupby("team")[["cost", "sqo"]].sum()
    check("event full-period cost/SQO $", tc.loc["event", "cost"] / tc.loc["event", "sqo"], 7287, 0.005)
    check("regional full-period cost/SQO $", tc.loc["regional", "cost"] / tc.loc["regional", "sqo"], 3832, 0.005)

    # ---- hand-edited deck numbers (slides 5, 7, 11/12; fig1 endpoints) ----
    # (a) brand+search: share of the FY24->FY25 DELTA in Won (deck claim) vs share of TOTAL FY25 Won (Q&A)
    bs = fyp.loc[["paid_brand_search", "paid_search"]]
    check("brand+search share of TOTAL FY25 Won %",
          float((bs.won_FY25.sum()) / fyp.won_FY25.sum() * 100), 72.2, 0.005)
    # (b) brand_search FY25 demo->SQO at full precision (slide shows 57.3%)
    fdemo = d[d["program"] == "paid_brand_search"].groupby("fy")[["demo", "sqo"]].sum()
    check("brand demo->SQO FY25 % (exact)", fdemo.loc["FY25", "sqo"] / fdemo.loc["FY25", "demo"] * 100,
          57.35, 0.001)
    # (c) fig8 in-figure notes: FY25 vs FY24 cost/SQO ratios
    check("paid_search FY25/FY24 cost/SQO ratio", ups("paid_search", "FY25", "sqo") / ups("paid_search", "FY24", "sqo"),
          1.21, 0.005)
    check("paid_social FY25/FY24 cost/SQO ratio", ups("paid_social", "FY25", "sqo") / ups("paid_social", "FY24", "sqo"),
          0.75, 0.005)
    # (d) fig1 endpoint indices (Jun-25 monthly total / Jul-23 monthly total * 100)
    me = d.groupby("ym")[["sqo", "won"]].sum()
    check("fig1 SQO endpoint index", me.loc[pd.Period("2025-06"), "sqo"] / me.loc[pd.Period("2023-07"), "sqo"] * 100,
          171, 0.005)
    check("fig1 Won endpoint index", me.loc[pd.Period("2025-06"), "won"] / me.loc[pd.Period("2023-07"), "won"] * 100,
          191, 0.005)

    # ---- report ----
    n_fail = 0
    print("=" * 78)
    print("VERIFY_NUMBERS — headline numbers re-derived from RAW csv")
    print("=" * 78)
    for name, ok, obs, exp in results:
        n_fail += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} observed {obs:>12,.2f}  cited {exp:>12,.2f}")
    print(f"\n{len(results) - n_fail}/{len(results)} PASS")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
