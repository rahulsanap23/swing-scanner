# Swing scan — 2026-10-23
Status: **ok** — scan complete  
Generated 2026-10-23 21:15 IST

## Data checks
```
{
  "constituents": {
    "NIFTY50": "downloaded",
    "MIDCAP150": "downloaded",
    "SMALLCAP250": "downloaded",
    "MICROCAP250": "downloaded"
  },
  "prices": {
    "source": "Yahoo Finance (yfinance)",
    "requested": 705,
    "received": 700,
    "missing": [
      "BAGMANE",
      "DUMMYHEG",
      "DUMMYINGL1",
      "DUMMYINGL2",
      "DUMMYINXGN"
    ]
  },
  "nse_bhavcopy": {
    "days_ok": 22,
    "days_requested": 22,
    "failures": []
  },
  "surveillance": {
    "asm": "ok",
    "gsm": "ok",
    "esm": "ok",
    "fo_ban": "ok"
  }
}
```

## Market
Nifty 22600.0 | 20/50/200 EMA 22840.14 / 23229.4 / 23971.85 | 5d -1.73% | 21d -3.12% | VIX 16.86 (20.17% 5d) | breadth >50EMA 10.06%

## Nifty 50 — 0 passed of 50
NO TRADE — closest: TECHM (failed: named setup — no breakout / flag / pullback / inside bar / NR7 detected)
Funnel: universe 50 → enough price history 50 → price floor 50 → surveillance / T2T / F&O ban 50 → no repeated circuits 50 → liquidity 50 → primary uptrend (50 EMA, 200) 4 → 20 EMA 3 → 3M relative strength > 0 3 → RSI 40-75 3 → named setup 0 → not overextended 0 → ATR band 0 → stop within limit 0 → target & R:R 0 → position size 0

## Midcap 150 — 1 passed of 150
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| INDHOTEL | Inside bar near resistance | 781.75 | 795.79 | 764.21 | 874.74 | 62 | 2.5 | 4.5 |  |
Funnel: universe 150 → enough price history 142 → price floor 140 → surveillance / T2T / F&O ban 139 → no repeated circuits 139 → liquidity 122 → primary uptrend (50 EMA, 200) 8 → 20 EMA 7 → 3M relative strength > 0 7 → RSI 40-75 7 → named setup 2 → not overextended 2 → ATR band 2 → stop within limit 1 → target & R:R 1 → position size 1

## Smallcap 250 — 0 passed of 251
NO TRADE — closest: ANANDRATHI (failed: target & R:R — target only 1.0% away (resistance too close))
Funnel: universe 251 → enough price history 235 → price floor 228 → surveillance / T2T / F&O ban 225 → no repeated circuits 225 → liquidity 224 → primary uptrend (50 EMA, 200) 20 → 20 EMA 9 → 3M relative strength > 0 9 → RSI 40-75 8 → named setup 4 → not overextended 4 → ATR band 4 → stop within limit 2 → target & R:R 0 → position size 0

## Microcap 250 — 0 passed of 254
NO TRADE — closest: KMEW (failed: stop within limit — stop 6.3% below entry > 5%)
Funnel: universe 254 → enough price history 231 → price floor 226 → surveillance / T2T / F&O ban 222 → no repeated circuits 222 → liquidity 206 → primary uptrend (50 EMA, 200) 15 → 20 EMA 9 → 3M relative strength > 0 8 → RSI 40-75 7 → named setup 4 → not overextended 4 → ATR band 3 → stop within limit 0 → target & R:R 0 → position size 0
