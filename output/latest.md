# Swing scan — 2026-10-30
Status: **ok** — scan complete  
Generated 2026-10-30 20:08 IST

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
    "requested": 704,
    "received": 699,
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
Nifty 23053.1 | 20/50/200 EMA 22845.81 / 23159.66 / 23916.0 | 5d 2.0% | 21d 1.48% | VIX 15.3 (-9.24% 5d) | breadth >50EMA 16.79%

## Nifty 50 — 2 passed of 50
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| ADANIPORTS | Inside bar near resistance | 1850.0 | 1875.34 | 1798.67 | 2062.88 | 26 | 2.45 | 4.5 |  |
| KOTAKBANK | Pullback to 20 EMA | 461.6 | 461.6 | 446.78 | 498.66 | 108 | 2.5 | 4.0 |  |
Funnel: universe 50 → enough price history 50 → price floor 50 → surveillance / T2T / F&O ban 50 → no repeated circuits 50 → liquidity 50 → primary uptrend (50 EMA, 200) 10 → 20 EMA 10 → 3M relative strength > 0 9 → RSI 40-75 8 → named setup 5 → not overextended 5 → ATR band 4 → stop within limit 4 → target & R:R 2 → position size 2

## Midcap 150 — 1 passed of 150
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| NYKAA | NR7 near resistance | 349.35 | 355.21 | 339.51 | 390.73 | 127 | 2.26 | 4.5 |  |
Funnel: universe 150 → enough price history 143 → price floor 141 → surveillance / T2T / F&O ban 140 → no repeated circuits 140 → liquidity 122 → primary uptrend (50 EMA, 200) 19 → 20 EMA 17 → 3M relative strength > 0 17 → RSI 40-75 16 → named setup 7 → not overextended 6 → ATR band 6 → stop within limit 5 → target & R:R 1 → position size 1

## Smallcap 250 — 1 passed of 251
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| GESHIP | Inside bar near resistance | 1593.6 | 1633.26 | 1560.11 | 1789.01 | 27 | 2.13 | 4.0 |  |
Funnel: universe 251 → enough price history 235 → price floor 229 → surveillance / T2T / F&O ban 226 → no repeated circuits 226 → liquidity 224 → primary uptrend (50 EMA, 200) 34 → 20 EMA 29 → 3M relative strength > 0 28 → RSI 40-75 28 → named setup 10 → not overextended 8 → ATR band 8 → stop within limit 4 → target & R:R 1 → position size 1

## Microcap 250 — 1 passed of 253
| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |
|---|---|---|---|---|---|---|---|---|---|
| SHREEJISPG | Inside bar near resistance | 843.3 | 847.39 | 810.11 | 932.13 | 53 | 2.27 | 4.0 | ⚠ASM (long-term, stage unknown — verify) |
Funnel: universe 253 → enough price history 232 → price floor 227 → surveillance / T2T / F&O ban 223 → no repeated circuits 222 → liquidity 206 → primary uptrend (50 EMA, 200) 20 → 20 EMA 17 → 3M relative strength > 0 17 → RSI 40-75 17 → named setup 9 → not overextended 9 → ATR band 7 → stop within limit 2 → target & R:R 1 → position size 1
