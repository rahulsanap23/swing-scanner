# Swing Scanner — daily Indian swing-trade shortlist

A free GitHub Actions job screens the Nifty 50, Midcap 150, Smallcap 250 and Microcap 250
every weekday evening. A daily Claude task then reads the results, does the judgment checks
(market context, fundamentals, news, events) and sends you a short shortlist.

```
7:15 PM IST  GitHub Actions ── screener.py ──▶ output/latest.json + latest.md
                                (Yahoo Finance EOD candles, NSE bhavcopy & surveillance lists)
~8:40 PM IST Claude scheduled task ── reads latest.json + prompt/daily_prompt.md
                                ── web checks on ~15–20 stocks ──▶ your shortlist (push/email)
```

## Setup (about 10 minutes)

1. **Create a GitHub repo**, e.g. `swing-scanner`.
   - *Public* is simplest: Actions minutes are free and Claude can read it with no extra access.
     Note that anyone could then see `config.yaml` (your capital and risk settings) and the scan output.
   - *Private* also works within GitHub's free monthly minutes (this job uses roughly 5–10 minutes
     a day); Claude then needs access to the repo through your GitHub connection.
2. **Upload all files** from this folder, keeping the folder structure
   (`.github/workflows/daily-scan.yml` must stay at that path).
3. **Allow the job to save results:** repo **Settings → Actions → General → Workflow permissions →
   Read and write permissions → Save**.
4. **Optional:** add the four index lists to `data/constituents/` (see the README there). The job
   downloads them itself; these copies are only a fallback if niftyindices.com blocks GitHub.
5. **Run it once:** **Actions → daily-swing-scan → Run workflow**. After it finishes (5–10 min),
   open `output/latest.md`.
   - Run it after 7 PM IST on a trading day. Earlier, today's data isn't out yet and the file will
     say `no_data_today`, which is expected.
6. **Send Claude the repo URL** so it can set up the daily scheduled task.

## What each part checks

| Prompt step | Done by | How |
|---|---|---|
| Exclusions: price < ₹30, repeated circuits, T2T/BE series, GSM, ESM, long-term ASM II+, F&O ban | screener | NSE files; anything NSE blocks is marked "unverified" for Claude to check |
| Exclusions: promoter pledge, auditor exit, SEBI action, insolvency | Claude | web |
| Step 1 market context | both | Nifty EMAs / VIX / breadth from the script; flows, sectors, global cues, events from the web |
| Steps 2–5 liquidity, trend, RS, RSI, setup, overextension, ATR, stop, target, R:R, qty | screener | code |
| Step 6 fundamentals, Step 7 events | Claude | web, only for the stocks the script passed |

Settings (capital, risk %, max position, thresholds per category) live in `config.yaml`.

## Output

- `output/latest.json` — what Claude reads. Per category: ranked candidates with the full trade
  plan and flags, a **funnel** (how many stocks survived each filter), and the **closest miss**
  when nothing passed. The funnel shows which filter is cutting the most stocks.
- `output/latest.md` — the same, readable on GitHub.
- `output/history/YYYY-MM-DD.json` — one file per day.

## Things to know

- **Free data can fail.** Yahoo sometimes throttles requests, and NSE sometimes blocks
  overseas servers like GitHub's. The script retries; NSE checks it can't get are marked
  `unverified` instead of guessed, and Claude verifies them.
- **Pattern detection is rule-based.** 52-week-high breakouts, base breakouts, pullbacks
  to the 20 EMA, inside bars and NR7 are exact rules. Flags/pennants are approximated as a
  strong move followed by a tight 5-day range. Post-results breakouts are judged by Claude.
- **Entries:** breakouts and pullbacks use today's close. Inside bar, NR7 and flag setups use
  a trigger just above the high ("buy above"), and only count if the trigger is within 1 ATR of the close.
- **Stops:** below the 5-day swing low when it is 1–2 ATR away; otherwise 1× or 1.5× ATR. A
  stop wider than 5% rejects the stock.
- **Targets:** just below the nearest resistance, capped at 10%; 2.5R if there is no resistance
  overhead. The target must be ≥3% (Nifty 50) or ≥4% (others) away, with R:R ≥ 2.
- **Quantity:** the lower of risk-based size and ₹50,000 ÷ entry.
- GitHub can pause scheduled workflows in a public repo after 60 days with no activity. If the
  daily run stops, re-enable it from the Actions tab.
- The logic was tested on generated data (`tests/`). Check `output/latest.md` after the first
  live runs.

## Run it on your own computer

```
pip install -r requirements.txt
python screener.py                     # today's scan
python screener.py --asof 2026-10-22   # re-run a past trading day
python -m pytest -q tests              # offline tests
```

Research candidates only, not buy advice.
