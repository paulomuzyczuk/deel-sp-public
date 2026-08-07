# Assumptions & Cleaning Decisions Log

Running log of every assumption and cleaning decision, in chronological order.
Each entry states the decision, the evidence, and where it is implemented.

## Phase 0 — Cleaning pipeline (data-cleaning/clean.py)

1. **Header normalization.** Raw headers contain UTF-8 non-breaking spaces
   (`\xa0`) in `# Marketing Qualified Prospects` and `# Sales Qualified
   Opportunities` (verified at byte level). All headers are normalized on load
   (`\xa0` → space, collapse whitespace) before any other processing, then
   renamed to snake_case working names.

2. **Cost parsing.** `$ Cost` is a string with `$` and thousand separators
   (e.g. `"$160,756"`). Parsed to float; the parser rejects any value that is
   not purely numeric after stripping `$` and `,` (none found — all 11,952
   values parsed).

3. **Duplicate (date, program) rows → sum-aggregation.** 52 rows (26 keys)
   on programs `regional` and `website`, dated 2025-06-18 to 2025-06-30.
   Verified pattern: every duplicate key has exactly ONE non-zero row; the
   second row is all-zero. Aggregating by sum therefore preserves the real
   values exactly. Safety check in clean.py stops the pipeline if any
   duplicate key ever has ≥2 non-zero rows.

4. **Team label repair (new finding, not in original audit).** The all-zero
   duplicate rows carry a WRONG team label: `lifecycle` instead of
   `regional`/`website`. Team is resolved to the program's majority value
   (regional: 731 vs 13 rows; website: 731 vs 13). clean.py verifies the
   minority-team rows are all-zero duplicates before repairing, and stops
   otherwise. Related observation: `paid_other` has no rows for exactly the
   same 13 dates (2025-06-18..2025-06-30) — consistent with a single ETL
   defect in the final 13 days of the data. No analysis impact
   (`paid_other` is all-zero and excluded), recorded for provenance.

5. **clicks > impressions rows flagged, not deleted.** 35 rows on `abm`,
   `paid_sponsorship`, `paid_awareness` get `flag_clicks_gt_impressions =
   True`. On all 35 rows impressions are 0–68 while clicks are large →
   impression-tracking dropout, not click inflation. These rows are excluded
   from CTR calculations only; their funnel metrics remain usable.

6. **ooh and paid_other excluded via flag.** Both programs have zero cost and
   zero outcomes on every row (sum of all metrics = 0 across 961 rows).
   Flagged `flag_excluded = True` with reason; rows are kept in the output so
   the exclusion is transparent and reversible.

7. **Fractional SQO / Won preserved.** 974 rows with fractional SQO, 419 with
   fractional Won — expected output of fractional multi-touch attribution.
   Not rounded, stored as float.

8. **Fiscal year Jul–Jun.** FY24 = 2023-07-01..2024-06-30, FY25 =
   2024-07-01..2025-06-30. Assignment raises on any date outside the range
   (none found). Helper columns `fiscal_year`, `year_month`, `is_paid` added.

9. **Daily grain preserved.** clean_daily.csv is one row per (date, program);
   all aggregation happens in the analysis layer. Post-clean assertions:
   unique keys, all metrics ≥ 0. Full per-program date coverage is NOT
   asserted (flighted programs legitimately have gaps).

10. **Output determinism.** Fixed sort order, fixed column order, LF line
    endings → running clean.py twice produces byte-identical output
    (verified by diff).

## Phase 1 — Task 1 analysis (analysis/task1_funnel_seasonality.ipynb)

11. **Aggregation grain.** All conversion rates are computed at monthly grain or
    coarser, never daily (funnel-lag: stages are not same-day cohorts). FY-level
    rates are ratios of FY sums, not averages of monthly rates. Day-of-week
    analysis uses daily grain for VOLUMES only, never rates.

12. **MQP restriction (user-approved).** MQP tracking is zero for all programs
    before 2024-01-03 (all programs start 2024-02-26) — a structural tracking
    artifact found in Phase 1 and verified against the raw file. MQP is analyzed
    from 2024-03 (first complete month) onward only; FY24-vs-FY25 MQP YoY is
    suppressed as not comparable; MQP is excluded from the indexed trend chart
    and from the both-years seasonality rule (insufficient history).

13. **Analysis universe.** `flag_excluded` rows (ooh, paid_other) are dropped.
    CTR calculations additionally drop `flag_clicks_gt_impressions` rows.
    `paid_sponsorship` and `abm` are excluded from any CTR narrative entirely
    (2025 month-start click batch-dumps; possible tracking artifact).

14. **Both-years seasonality rule.** A monthly pattern counts as recurring
    seasonal only if the same calendar month deviates in the same direction from
    its centered 12-month rolling mean (window 13, min 6 months at series edges)
    in BOTH observed years, with |deviation| > 5% in both. One-year patterns are
    labeled one-off events. Edge months use partial windows (documented caveat:
    some trend leakage possible; the both-years rule is the guard).

15. **Channel deep-dive selection.** paid_search / paid_brand_search /
    paid_social: the only always-on programs with full impression→click→demo→SQO
    coverage, forming a demand-capture vs branded-capture vs awareness contrast.
    Non-paid channels carry no impressions/clicks (ineligible by construction);
    abm/paid_sponsorship excluded for click-dump artifacts, paid_awareness for
    flighting + near-zero bottom-funnel, listicle_leadbuy_listing as a
    structurally different lead-buy.

16. **Rate definitions.** CTR = clicks/impressions; click→demo = demo/clicks;
    demo→SQO = sqo/demo — all monthly-or-coarser period ratios (not cohort
    rates). cost per SQO = cost/sqo on FY sums.

17. **Indexed trend chart.** Base = Jul 2023 = 100 (user-picked design);
    impressions/clicks are paid-only; Jan-2024 clicks spike annotated as the
    paid_social delivery burst (one-off event, verified: 7.48M clicks, 660M
    impressions, cost +94% vs Dec).

18. **Team YoY overlays** use the largest teams by SQO (paid, content,
    lifecycle, event). Every website view carries the 2023-11 demo-shift caveat
    (candidate tracking change, hypothesis — not interpretable as real decline
    without a tagging audit).

19. **Verification.** A notebook cell re-computes and asserts every number cited
    in findings; `analysis/verify_numbers.py` independently re-derives all 39
    headline numbers from the RAW csv (own cleaning code) — 39/39 PASS.

## Phase 2 — Task 2 analysis (analysis/task2_cost_brand.ipynb)

20. **Attributed-credit language.** All SQO/Won figures in Task 2 are phrased as
    fractional attributed credit; every ratio is a period ratio (funnel-lag
    caveat), never a cohort rate, never causal.

21. **Rider A volume threshold.** Per-program SQO→Won comparisons restricted to
    programs with ≥ 100 attributed SQO in BOTH fiscal years (10 of 15 programs,
    99.8% of SQO volume). Decomposition (within-program vs mix) drops
    paid_awareness (zero SQO in FY24; 6 SQO in FY25).

22. **fig1 title scoped (Rider B).** "Flat traffic" claim now explicitly scoped
    to paid impressions & clicks in the title itself.

23. **2.1 channel selection.** paid_search + paid_social = largest non-branded
    spend with a capture-vs-awareness contrast; paid_brand_search analyzed
    separately (harvesting confound); listicle in the 2.5 ranking only
    (structurally different lead-buy); abm/sponsorship/awareness not SQO-scale.

24. **paid_search step-up dated from data.** The brief said 2024-09; the
    observed spend/impressions step is 2024-10 (cost $5.7M Sep → $8.3M Oct) —
    the analysis uses the observed month and notes the discrepancy.
    Before/after windows: Oct-23..Sep-24 vs Oct-24..Jun-25 (monthly means).
    Marginal cost per incremental attributed SQO is arithmetic association,
    not incrementality.

25. **Diminishing-returns view.** No fitted line (24 noisy monthly points,
    non-iid residuals): spend-tercile cost-weighted aggregates + Spearman rank
    correlation instead. Both channels show ρ ≈ +0.42 overall, driven by FY25
    (search +0.78, social +0.76 within-FY25).

26. **Cost geography correction (found in Phase 2).** Not all non-paid teams
    are zero-cost: event ($9.5M) and regional ($4.3M) carry spend. The 2.3
    "zero-cost brand/organic" group is exactly content/website/social/lifecycle
    (asserted zero cost in-notebook); event/regional noted separately in 2.5.

27. **brand_search Act 2 exhibit.** Quarterly spend vs cost-per-attributed-SQO
    trajectory with the demand-harvesting caveat rendered inside the figure;
    incremental cost per SQO is stated to be HIGHER than attributed cost per
    SQO if harvesting exists.

28. **Verification extended.** verify_numbers.py now re-derives 75 headline
    numbers (Tasks 1 + 2) from the raw CSV — 75/75 PASS.

29. **Figure styling moved onto the Deel brand surface.** All figures are now
    generated with `presentation/visual-resources/palette/deel.mplstyle`, so the
    chart canvas is latte `#FFFBF4` — identical to the slide background. The
    previous near-white `#FCFCFB` canvas rendered as a visible pale rectangle on
    every chart slide. Ink/grid/baseline colours are Deel's alpha border and
    content tokens composited onto latte (`#DAD7D1`, `#A4A19D`, `#5F5E5C`).
    No data, aggregation or number changed — the verification cell still passes.

30. **Series colour roles (analysis decision, not decoration).** Series are
    assigned from the validated Deel categorical palette in a fixed order by
    entity, never by rank: prospects/paid_social `#2187CF`, demo `#15740F`,
    SQO/paid_search `#5938B7` (acai, the primary), won/paid_brand_search
    `#C98A00`. Both colour sets were run through the colour-vision-deficiency
    validator against the latte surface: the three-channel legend in fig5 passes
    on *all* pairs, and fig1's ladder passes on adjacent pairs. `#C98A00` sits
    below 3:1 contrast on latte, which is why every series in fig1 also carries
    a direct end-of-line label — identity is never carried by colour alone.
    Fig6 uses Deel's acai ramp light→dark for magnitude.
