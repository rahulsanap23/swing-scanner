# Swing scan — 2026-10-28
Status: **ok** — scan complete  
Generated 2026-10-28 20:06 IST

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
Nifty 22698.85 | 20/50/200 EMA 22812.12 / 23173.28 / 23934.6 | 5d -0.49% | 21d -1.91% | VIX 16.25 (3.6% 5d) | breadth >50EMA 19.25%

## Nifty 50 — 0 passed of 50
NO TRADE — closest: DRREDDY (failed: target & R:R — target only 2.5% away (resistance too close))
Funnel: universe 50 → enough price history 50 → price floor 50 → surveillance / T2T / F&O ban 50 → no repeated circuits 50 → liquidity 50 → primary uptrend (50 EMA, 200) 8 → 20 EMA 8 → 3M relative strength > 0 8 → RSI 40-75 8 → named setup 3 → not overextended 3 → ATR band 2 → stop within limit 2 → target & R:R 0 → position size 0

## Midcap 150 — 2 passed of 150
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| INDHOTEL | NR7 near resistance | 805.2 | 816.93 | 785.02 | 896.71 | 61 | 2.5 | 4.5 |  |
| LAURUSLABS | Pullback to 20 EMA | 2181.9 | 2181.9 | 2090.92 | 2400.09 | 21 | 2.4 | 3.0 |  |
Funnel: universe 150 → enough price history 142 → price floor 140 → surveillance / T2T / F&O ban 139 → no repeated circuits 139 → liquidity 122 → primary uptrend (50 EMA, 200) 16 → 20 EMA 15 → 3M relative strength > 0 15 → RSI 40-75 15 → named setup 6 → not overextended 5 → ATR band 5 → stop within limit 5 → target & R:R 2 → position size 2

## Smallcap 250 — 0 passed of 251
NO TRADE — closest: ATHERENERG (failed: stop within limit — stop 6.8% below entry > 5%)
Funnel: universe 251 → enough price history 235 → price floor 229 → surveillance / T2T / F&O ban 226 → no repeated circuits 226 → liquidity 225 → primary uptrend (50 EMA, 200) 42 → 20 EMA 38 → 3M relative strength > 0 37 → RSI 40-75 36 → named setup 10 → not overextended 9 → ATR band 9 → stop within limit 0 → target & R:R 0 → position size 0

## Microcap 250 — 1 passed of 254
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| SHREEJISPG | Pullback to 20 EMA | 840.3 | 840.3 | 801.02 | 924.33 | 50 | 2.14 | 3.5 | ⚠ASM (long-term, stage unknown — verify) |
Funnel: universe 254 → enough price history 231 → price floor 226 → surveillance / T2T / F&O ban 222 → no repeated circuits 220 → liquidity 204 → primary uptrend (50 EMA, 200) 25 → 20 EMA 20 → 3M relative strength > 0 20 → RSI 40-75 20 → named setup 9 → not overextended 8 → ATR band 8 → stop within limit 2 → target & R:R 1 → position size 1
