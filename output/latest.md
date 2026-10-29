# Swing scan — 2026-10-29
Status: **ok** — scan complete  
Generated 2026-10-29 20:07 IST

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
Nifty 22936.75 | 20/50/200 EMA 22823.99 / 23164.01 / 23925.57 | 5d 1.1% | 21d 0.69% | VIX 15.12 (-4.08% 5d) | breadth >50EMA 21.84%

## Nifty 50 — 1 passed of 50
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| KOTAKBANK | 52-week high breakout | 459.0 | 459.0 | 443.71 | 497.22 | 108 | 2.5 | 5.18 |  |
Funnel: universe 50 → enough price history 50 → price floor 50 → surveillance / T2T / F&O ban 50 → no repeated circuits 50 → liquidity 50 → primary uptrend (50 EMA, 200) 9 → 20 EMA 9 → 3M relative strength > 0 9 → RSI 40-75 9 → named setup 8 → not overextended 8 → ATR band 6 → stop within limit 6 → target & R:R 1 → position size 1

## Midcap 150 — 3 passed of 150
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| LAURUSLABS | 52-week high breakout | 2244.0 | 2244.0 | 2151.16 | 2468.4 | 21 | 2.42 | 5.79 |  |
| INDHOTEL | NR7 near resistance | 810.0 | 817.98 | 787.03 | 895.37 | 61 | 2.5 | 4.5 |  |
| NYKAA | Pullback to 20 EMA | 352.9 | 352.9 | 336.77 | 388.19 | 124 | 2.19 | 3.5 |  |
Funnel: universe 150 → enough price history 142 → price floor 140 → surveillance / T2T / F&O ban 139 → no repeated circuits 139 → liquidity 122 → primary uptrend (50 EMA, 200) 22 → 20 EMA 21 → 3M relative strength > 0 19 → RSI 40-75 19 → named setup 12 → not overextended 11 → ATR band 11 → stop within limit 9 → target & R:R 3 → position size 3

## Smallcap 250 — 3 passed of 251
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| GESHIP | Base breakout on volume | 1618.8 | 1618.8 | 1546.09 | 1780.68 | 27 | 2.23 | 5.72 |  |
| SONACOMS | NR7 near resistance | 873.6 | 887.57 | 843.83 | 976.33 | 45 | 2.03 | 4.0 |  |
| ANANDRATHI | Inside bar near resistance | 2270.0 | 2287.17 | 2209.58 | 2481.13 | 21 | 2.5 | 4.0 |  |
Funnel: universe 251 → enough price history 235 → price floor 229 → surveillance / T2T / F&O ban 226 → no repeated circuits 226 → liquidity 225 → primary uptrend (50 EMA, 200) 43 → 20 EMA 39 → 3M relative strength > 0 39 → RSI 40-75 38 → named setup 16 → not overextended 15 → ATR band 14 → stop within limit 4 → target & R:R 3 → position size 3

## Microcap 250 — 0 passed of 254
NO TRADE — closest: LUMAXTECH (failed: stop within limit — stop 7.1% below entry > 5%)
Funnel: universe 254 → enough price history 231 → price floor 226 → surveillance / T2T / F&O ban 222 → no repeated circuits 221 → liquidity 205 → primary uptrend (50 EMA, 200) 31 → 20 EMA 23 → 3M relative strength > 0 21 → RSI 40-75 21 → named setup 8 → not overextended 7 → ATR band 5 → stop within limit 0 → target & R:R 0 → position size 0
