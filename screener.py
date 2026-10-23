#!/usr/bin/env python3
"""
Daily Indian swing-trade screener.

Does the number-crunching steps of the swing prompt with code:
  Step 2 liquidity, Step 3 trend, Step 4 setup, Step 5 volatility / stop /
  target / R:R / quantity, plus the exclusions that can be checked from
  exchange files (price floor, circuits, T2T series, GSM/ESM/ASM, F&O ban).

Universe: Nifty 50, Midcap 150, Smallcap 250, Microcap 250.
Output:   output/latest.json and output/latest.md (plus a dated copy in
          output/history/). A daily Claude task reads these and does the
          judgment steps: market context, fundamentals, news and events.

Data sources (all free): Yahoo Finance via yfinance (daily candles),
NSE archives (bhavcopy with delivery %, F&O ban), NSE surveillance reports,
Nifty Indices constituent lists. Every exchange download fails soft: if it
can't be fetched, the affected check is marked "unverified" instead of guessed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import re
import sys
import time
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
IST = ZoneInfo("Asia/Kolkata")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
SCHEMA_VERSION = 1
T2T_SERIES = {"BE", "BZ", "BT"}          # trade-to-trade / restricted series
NIFTY_TICKER, VIX_TICKER = "^NSEI", "^INDIAVIX"

STEPS = [
    "enough price history",
    "price floor",
    "surveillance / T2T / F&O ban",
    "no repeated circuits",
    "liquidity",
    "primary uptrend (50 EMA, 200)",
    "20 EMA",
    "3M relative strength > 0",
    "RSI 40-75",
    "named setup",
    "not overextended",
    "ATR band",
    "stop within limit",
    "target & R:R",
    "position size",
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def r2(x):
    """Round for output; keep None/NaN as None so JSON stays valid."""
    if x is None:
        return None
    try:
        if isinstance(x, (float, np.floating)) and (math.isnan(x) or math.isinf(x)):
            return None
        return round(float(x), 2)
    except (TypeError, ValueError):
        return x


def log(msg: str) -> None:
    print(f"[{dt.datetime.now(IST):%H:%M:%S}] {msg}", flush=True)


def http_client():
    import httpx
    return httpx.Client(
        http2=True, timeout=30.0, follow_redirects=True,
        headers={"User-Agent": UA, "Accept": "*/*",
                 "Accept-Language": "en-US,en;q=0.9",
                 "Referer": "https://www.nseindia.com/"})


def http_get(client, url: str, tries: int = 3, pause: float = 1.5):
    last = "no response"
    for i in range(tries):
        try:
            r = client.get(url)
            if r.status_code == 200 and r.content:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as e:  # network errors, timeouts
            last = f"{type(e).__name__}: {e}"
        time.sleep(pause * (i + 1))
    raise RuntimeError(f"{url} -> {last}")


# --------------------------------------------------------------------------
# data loading (network)
# --------------------------------------------------------------------------
def parse_constituents(text: str) -> list[str]:
    df = pd.read_csv(io.StringIO(text))
    cols = {c.strip().lower(): c for c in df.columns}
    if "symbol" not in cols:
        raise ValueError(f"no Symbol column in constituent file (columns: {list(df.columns)})")
    syms = df[cols["symbol"]].astype(str).str.strip().str.upper()
    return [s for s in syms if s and s != "NAN"]


def load_constituents(cfg: dict, client, refresh: bool = True):
    """Download each index list; fall back to the copy saved in the repo."""
    cdir = ROOT / "data" / "constituents"
    cdir.mkdir(parents=True, exist_ok=True)
    out, status = {}, {}
    for key, cat in cfg["categories"].items():
        path = cdir / cat["file"]
        how, err = None, None
        if refresh and client is not None:
            for url in cat.get("urls", []):
                try:
                    r = http_get(client, url, tries=2)
                    text = r.content.decode("utf-8-sig", errors="replace")
                    syms = parse_constituents(text)
                    if len(syms) >= 0.8 * cat.get("expected_size", 1):
                        path.write_text(text, encoding="utf-8")
                        how = "downloaded"
                        break
                    err = f"only {len(syms)} symbols"
                except Exception as e:
                    err = str(e)[:160]
        if path.exists():
            out[key] = parse_constituents(path.read_text(encoding="utf-8-sig"))
            if how:
                status[key] = "downloaded"
            elif refresh:
                status[key] = f"saved copy (download failed: {err})"
            else:
                status[key] = "saved copy"
        else:
            out[key] = []
            status[key] = f"MISSING (download failed: {err})"
    return out, status


def _frame_for(data: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    """Pull one ticker's OHLCV out of a yfinance download, whatever its column layout."""
    if data is None or data.empty:
        return None
    cols = data.columns
    if isinstance(cols, pd.MultiIndex):
        if ticker in cols.get_level_values(0):
            df = data[ticker]
        elif ticker in cols.get_level_values(1):
            df = data.xs(ticker, axis=1, level=1)
        else:
            return None
    else:
        df = data
    df = df.rename(columns=lambda c: str(c).strip().lower())
    need = ["open", "high", "low", "close", "volume"]
    if not all(c in df.columns for c in need):
        return None
    df = df[need].apply(pd.to_numeric, errors="coerce").dropna(subset=["close", "high", "low"])
    if df.empty:
        return None
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert(IST).tz_localize(None)
    df.index = idx.normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df["volume"] = df["volume"].fillna(0)
    return df.astype(float)


def fetch_prices(tickers: list[str], period: str, chunk: int = 50, pause: float = 2.5):
    """Daily OHLCV from Yahoo, in batches with retries. Prices are split-adjusted,
    not dividend-adjusted, so the latest close matches the real market price."""
    import yfinance as yf

    def download(batch):
        for attempt in range(3):
            try:
                return yf.download(batch, period=period, interval="1d", group_by="ticker",
                                   auto_adjust=False, actions=False, threads=True,
                                   progress=False)
            except Exception as e:
                log(f"  yahoo batch error ({type(e).__name__}); retry {attempt + 1}")
                time.sleep(10 * (attempt + 1))
        return None

    frames: dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), chunk):
        batch = tickers[i:i + chunk]
        data = download(batch)
        for t in batch:
            df = _frame_for(data, t)
            if df is not None and len(df) > 0:
                frames[t] = df
        log(f"  prices: {min(i + chunk, len(tickers))}/{len(tickers)} requested, {len(frames)} received")
        time.sleep(pause)
    # second pass for anything missing, one at a time (capped so an outage can't stall the job)
    for t in [t for t in tickers if t not in frames][:80]:
        time.sleep(1.5)
        df = _frame_for(download([t]), t)
        if df is not None and len(df) > 0:
            frames[t] = df
    return frames


def fetch_bhavcopies(client, dates: list[dt.date]):
    """NSE 'full' bhavcopy (has series, turnover and delivery %) for the given dates."""
    frames, fails = [], []
    for d in dates:
        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d:%d%m%Y}.csv"
        try:
            r = http_get(client, url, tries=2, pause=2.0)
            df = pd.read_csv(io.StringIO(r.text), skipinitialspace=True)
            df.columns = [str(c).strip().upper() for c in df.columns]
            for c in ("SYMBOL", "SERIES"):
                df[c] = df[c].astype(str).str.strip().str.upper()
            for c in ("CLOSE_PRICE", "TTL_TRD_QNTY", "TURNOVER_LACS", "DELIV_QTY", "DELIV_PER"):
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["DATE"] = pd.Timestamp(d)
            frames.append(df[["DATE", "SYMBOL", "SERIES", "CLOSE_PRICE", "TTL_TRD_QNTY",
                              "TURNOVER_LACS", "DELIV_QTY", "DELIV_PER"]])
        except Exception as e:
            fails.append(f"{d}: {str(e)[:120]}")
        time.sleep(0.7)
    return (pd.concat(frames, ignore_index=True) if frames else None), fails


def _walk_symbols(obj, path=()):
    """Yield (symbol, path, record) for every dict with a 'symbol' key inside NSE JSON."""
    if isinstance(obj, dict):
        keys = {str(k).lower(): k for k in obj}
        if "symbol" in keys and isinstance(obj[keys["symbol"]], str):
            yield obj[keys["symbol"]].strip().upper(), path, obj
        for k, v in obj.items():
            yield from _walk_symbols(v, path + (str(k),))
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_symbols(v, path)


def _stage_of(record: dict):
    for k, v in record.items():
        if "stage" in str(k).lower() and v not in (None, ""):
            s = str(v).upper()
            roman = {"IV": 4, "III": 3, "II": 2, "I": 1}
            m = re.search(r"\b(IV|III|II|I)\b", s)
            if m:
                return roman[m.group(1)]
            m = re.search(r"(\d)", s)
            if m:
                return int(m.group(1))
    return None


def parse_asm(js) -> dict:
    out = {}
    for sym, path, rec in _walk_symbols(js):
        p = " ".join(path).lower()
        term = "long" if ("long" in p or re.search(r"\blt", p)) else \
               "short" if ("short" in p or re.search(r"\bst", p)) else "unknown"
        out[sym] = {"list": "ASM", "term": term, "stage": _stage_of(rec)}
    return out


def parse_simple_list(js, name: str) -> dict:
    return {sym: {"list": name, "stage": _stage_of(rec)} for sym, _, rec in _walk_symbols(js)}


def parse_fo_ban(text: str) -> set[str]:
    syms = set()
    for line in text.splitlines():
        parts = [p.strip().upper() for p in line.split(",") if p.strip()]
        if len(parts) >= 2 and parts[0].isdigit() and re.fullmatch(r"[A-Z0-9&\-]+", parts[-1]):
            syms.add(parts[-1])
    return syms


def fetch_surveillance(client) -> dict:
    """Best effort. Each list is None when it couldn't be fetched (= unverified)."""
    res = {"asm": None, "gsm": None, "esm": None, "fo_ban": None, "errors": {}}
    try:
        client.get("https://www.nseindia.com/")          # NSE needs session cookies
        time.sleep(1.5)
    except Exception as e:
        res["errors"]["cookies"] = str(e)[:120]
    for key, url, parser in [
        ("asm", "https://www.nseindia.com/api/reportASM", parse_asm),
        ("gsm", "https://www.nseindia.com/api/reportGSM", lambda j: parse_simple_list(j, "GSM")),
        ("esm", "https://www.nseindia.com/api/reportESM", lambda j: parse_simple_list(j, "ESM")),
    ]:
        try:
            res[key] = parser(http_get(client, url, tries=2, pause=2.0).json())
        except Exception as e:
            res["errors"][key] = str(e)[:160]
        time.sleep(1.0)
    try:
        r = http_get(client, "https://nsearchives.nseindia.com/content/fo/fo_secban.csv", tries=2)
        res["fo_ban"] = parse_fo_ban(r.text)
    except Exception as e:
        res["errors"]["fo_ban"] = str(e)[:160]
    return res


# --------------------------------------------------------------------------
# indicators
# --------------------------------------------------------------------------
def _wilder(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    c, h, l = df["close"], df["high"], df["low"]
    out = pd.DataFrame(index=df.index)
    out["ema20"] = c.ewm(span=20, adjust=False).mean()
    out["ema50"] = c.ewm(span=50, adjust=False).mean()
    out["ema200"] = c.ewm(span=200, adjust=False).mean()
    out["sma200"] = c.rolling(200).mean()

    delta = c.diff()
    avg_gain = _wilder(delta.clip(lower=0), 14)
    avg_loss = _wilder(-delta.clip(upper=0), 14)
    rsi = 100 - 100 / (1 + avg_gain / avg_loss)
    out["rsi"] = rsi.where(avg_loss != 0, 100.0)

    prev_close = c.shift()
    tr = pd.concat([h - l, (h - prev_close).abs(), (l - prev_close).abs()], axis=1).max(axis=1)
    atr = _wilder(tr, 14)
    out["atr"] = atr

    up, down = h.diff(), -l.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    plus_di = 100 * _wilder(plus_dm, 14) / atr
    minus_di = 100 * _wilder(minus_dm, 14) / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    out["adx"] = _wilder(dx, 14)

    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    out["macd"] = macd
    out["macd_signal"] = macd.ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    return out


def pivot_highs(high: pd.Series, left: int = 5, right: int = 5) -> list[float]:
    h = high.to_numpy()
    return [h[i] for i in range(left, len(h) - right)
            if h[i] == h[i - left:i + right + 1].max()]


def count_circuit_days(df: pd.DataFrame, sessions: int = 10) -> int:
    """Days closing at the day's high/low with a move of ~2/5/10/20% (typical circuit bands)."""
    pct = df["close"].pct_change() * 100
    n = 0
    for i in range(-sessions, 0):
        p, cl, hi, lo = pct.iloc[i], df["close"].iloc[i], df["high"].iloc[i], df["low"].iloc[i]
        if pd.isna(p):
            continue
        near_band = any(abs(abs(p) - b) <= 0.15 for b in (2, 5, 10, 20))
        at_extreme = (p > 0 and cl >= hi * 0.999) or (p < 0 and cl <= lo * 1.001)
        n += int(near_band and at_extreme)
    return n


def detect_setups(df: pd.DataFrame, ind: pd.DataFrame, vol_x: float):
    """Return ([(name, family, entry_trigger or None)], volume_ratio). Ordered by preference."""
    c, o, h, l, v = (df[k] for k in ("close", "open", "high", "low", "volume"))
    C, O, H, L = c.iloc[-1], o.iloc[-1], h.iloc[-1], l.iloc[-1]
    atr, ema20 = ind["atr"].iloc[-1], ind["ema20"]
    vol20 = v.iloc[-21:-1].mean()
    vr = v.iloc[-1] / vol20 if vol20 > 0 else float("nan")
    hi20, lo20 = h.iloc[-21:-1].max(), l.iloc[-21:-1].min()
    hi252 = h.iloc[-253:-1].max()
    atr_pct = atr / C * 100
    found = []

    if C > hi252 and vr >= vol_x:
        found.append(("52-week high breakout", "breakout", None))
    base_range_pct = (hi20 / lo20 - 1) * 100 if lo20 > 0 else float("inf")
    if C > hi20 and vr >= vol_x and base_range_pct <= 7 * atr_pct:
        found.append(("Base breakout on volume", "breakout", None))

    if len(c) >= 30:
        # flag box = the 5 sessions before today; pole = the 20 sessions before the box
        pole = c.iloc[-7] / c.iloc[-27] - 1
        fh, fl = h.iloc[-6:-1].max(), l.iloc[-6:-1].min()
        box = max(fh, H) - min(fl, L)
        if pole >= 0.08 and box <= 2.5 * atr and C <= fh and C >= 0.95 * hi20:
            found.append(("Bull flag / tight consolidation", "consolidation", fh * 1.002))

    touched = bool((l.iloc[-3:] <= ema20.iloc[-3:] * 1.01).any())
    rising = ema20.iloc[-1] > ema20.iloc[-6]
    body, rng = abs(C - O), H - L
    lower_wick = min(C, O) - L
    bullish = (C > O and C > c.iloc[-2]) or (rng > 0 and lower_wick >= 2 * body and (C - L) / rng >= 0.6)
    if touched and rising and bullish and C >= ema20.iloc[-1] * 0.98:
        found.append(("Pullback to 20 EMA", "pullback", None))

    near_res = C >= 0.95 * hi20
    if H < h.iloc[-2] and L > l.iloc[-2] and near_res:
        found.append(("Inside bar near resistance", "consolidation", H * 1.002))
    ranges = (h - l).iloc[-7:]
    if ranges.iloc[-1] <= ranges.min() and near_res:
        found.append(("NR7 near resistance", "consolidation", H * 1.002))
    # a buy-above trigger only counts if it is within 1 ATR of today's close
    found = [s for s in found if s[2] is None or (s[2] - C) <= atr]
    return found, vr


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------
def bhav_stats(bhav: pd.DataFrame | None) -> dict:
    """Per symbol: latest series, 20-day avg turnover (₹ cr), 20-day avg delivery %."""
    if bhav is None or bhav.empty:
        return {}
    eq_like = bhav[~bhav["SERIES"].isin({"SM", "ST", "SZ"})]
    latest_date = eq_like["DATE"].max()
    out = {}
    for sym, g in eq_like.groupby("SYMBOL"):
        g = g.sort_values("DATE")
        last = g[g["DATE"] == g["DATE"].max()]
        series = "EQ" if (last["SERIES"] == "EQ").any() else last["SERIES"].iloc[0]
        tail = g[g["SERIES"].isin({"EQ"} | T2T_SERIES)].groupby("DATE").agg(
            turnover=("TURNOVER_LACS", "sum"), deliv=("DELIV_PER", "mean")).tail(20)
        out[sym] = {
            "series": series,
            "traded_today": bool(g["DATE"].max() == latest_date),
            "days": int(len(tail)),
            "adtv_cr": float(tail["turnover"].mean() / 100) if len(tail) else None,
            "delivery_pct": float(tail["deliv"].mean()) if tail["deliv"].notna().any() else None,
        }
    return out


def surveillance_status(sym: str, surv: dict):
    """-> (exclude_reason or None, flags list, unverified list)"""
    flags, unverified = [], []
    if surv.get("gsm") is None:
        unverified.append("GSM")
    elif sym in surv["gsm"]:
        return "in GSM", flags, unverified
    if surv.get("esm") is None:
        unverified.append("ESM")
    elif sym in surv["esm"]:
        return "in ESM", flags, unverified
    if surv.get("fo_ban") is None:
        unverified.append("F&O ban")
    elif sym in surv["fo_ban"]:
        return "in F&O ban list", flags, unverified
    if surv.get("asm") is None:
        unverified.append("ASM")
    elif sym in surv["asm"]:
        a = surv["asm"][sym]
        if a["term"] == "long" and (a["stage"] or 0) >= 2:
            return f"long-term ASM stage {a['stage']}", flags, unverified
        if a["term"] == "long" and a["stage"] is None:
            flags.append("⚠ASM (long-term, stage unknown — verify)")
        else:
            flags.append(f"⚠ASM ({a['term']}-term{' stage ' + str(a['stage']) if a['stage'] else ''})")
    return None, flags, unverified


def evaluate(sym: str, df: pd.DataFrame, cat: dict, cfg: dict, ctx: dict) -> dict:
    """Run every hard filter in order. Returns a record with steps_passed and either
    the trade plan (passed=True) or the first failed step and why."""
    rec = {"symbol": sym, "passed": False, "steps_passed": 0, "flags": [], "unverified": []}

    def fail(detail):
        rec["failed_step"], rec["fail_detail"] = STEPS[rec["steps_passed"]], detail
        return rec

    def ok():
        rec["steps_passed"] += 1

    # 1 history
    if df is None or len(df) < 260:
        return fail(f"only {0 if df is None else len(df)} daily bars")
    if df.index[-1].date() != ctx["data_date"]:
        return fail(f"last bar {df.index[-1].date()} (not traded on {ctx['data_date']})")
    ind = compute_indicators(df)
    last = ind.iloc[-1]
    if last[["ema20", "ema50", "ema200", "rsi", "atr", "adx", "macd"]].isna().any():
        return fail("indicators incomplete")
    ok()

    c = df["close"]
    C = float(c.iloc[-1])
    rec["cmp"] = C

    # 2 price floor
    if C < cfg["min_price"]:
        return fail(f"price ₹{C:.2f} < ₹{cfg['min_price']}")
    ok()

    # 3 surveillance / T2T / F&O ban
    b = ctx["bhav"].get(sym)
    if ctx["bhav_ok"]:
        if b is None:
            rec["unverified"].append("series/delivery (not in NSE bhavcopy)")
        elif b["series"] in T2T_SERIES:
            return fail(f"trade-to-trade series {b['series']}")
    else:
        rec["unverified"].append("T2T series")
    reason, sflags, sunv = surveillance_status(sym, ctx["surv"])
    rec["flags"] += sflags
    rec["unverified"] += sunv
    if reason:
        return fail(reason)
    ok()

    # 4 circuits
    if cat.get("check_circuits", True):
        n_circ = count_circuit_days(df)
        if n_circ >= 3:
            return fail(f"{n_circ} circuit-like closes in last 10 sessions")
    ok()

    # 5 liquidity
    if b and b.get("adtv_cr") is not None and b["days"] >= 10:
        adtv_cr, adtv_src = b["adtv_cr"], "NSE turnover"
    else:
        adtv_cr = float((c * df["volume"]).iloc[-20:].mean() / 1e7)
        adtv_src = "close×volume estimate"
    rec["adtv_cr"], rec["adtv_source"] = adtv_cr, adtv_src
    if adtv_cr < cat["min_adtv_cr"]:
        return fail(f"20-day avg traded value ₹{adtv_cr:.1f} cr < ₹{cat['min_adtv_cr']} cr")
    deliv = b.get("delivery_pct") if b else None
    rec["delivery_pct_20d"] = deliv
    if cat.get("min_delivery_pct"):
        if deliv is None:
            rec["unverified"].append("delivery %")
        elif deliv < cat["min_delivery_pct"]:
            return fail(f"20-day avg delivery {deliv:.1f}% < {cat['min_delivery_pct']}%")
    ok()

    e20, e50, e200, s200 = (float(last[k]) for k in ("ema20", "ema50", "ema200", "sma200"))
    # 6 primary uptrend
    if not (C > e50 and (e50 > e200 or (not math.isnan(s200) and C > 1.05 * s200))):
        return fail(f"close {C:.2f} / 50 EMA {e50:.2f} / 200 EMA {e200:.2f}")
    ok()

    setups, vol_ratio = detect_setups(df, ind, cat["breakout_volume_x"])
    rec["volume_ratio"] = vol_ratio
    primary = setups[0] if setups else None
    family = primary[1] if primary else None

    # 7 20 EMA (pullbacks may sit up to 2% below it)
    if not (C > e20 or (family == "pullback" and C >= 0.98 * e20)):
        return fail(f"close {(C / e20 - 1) * 100:.1f}% vs 20 EMA")
    ok()

    # 8 relative strength vs Nifty
    nifty = ctx["nifty_close"].reindex(df.index).ffill()

    def rel(n):
        return ((c.iloc[-1] / c.iloc[-1 - n]) / (nifty.iloc[-1] / nifty.iloc[-1 - n]) - 1) * 100
    rs1, rs3 = float(rel(21)), float(rel(63))
    rec["rs_1m_pct"], rec["rs_3m_pct"] = rs1, rs3
    if not rs3 > 0:
        return fail(f"3-month RS vs Nifty {rs3:.1f}%")
    ok()

    # 9 RSI
    rsi = float(last["rsi"])
    rec["rsi"] = rsi
    if not 40 <= rsi <= 75:
        return fail(f"RSI {rsi:.1f}")
    ok()

    # 10 setup
    if not primary:
        return fail("no breakout / flag / pullback / inside bar / NR7 detected")
    rec["setup"], rec["setup_family"] = primary[0], family
    rec["other_setups"] = [s[0] for s in setups[1:]]
    ok()

    # 11 overextension
    ext = (C / e20 - 1) * 100
    ret5 = (C / float(c.iloc[-6]) - 1) * 100
    rec["pct_above_ema20"], rec["ret_5d_pct"] = ext, ret5
    if ext > 10 or ret5 > 15:
        return fail(f"{ext:.1f}% above 20 EMA, {ret5:.1f}% in 5 sessions")
    ok()

    # 12 ATR band
    atr = float(last["atr"])
    atr_pct = atr / C * 100
    rec["atr_pct"] = atr_pct
    lo, hi = cat["atr_pct"]
    if not lo <= atr_pct <= hi:
        return fail(f"ATR {atr_pct:.2f}% outside {lo}-{hi}%")
    ok()

    # 13 entry & stop
    entry = float(primary[2]) if primary[2] else C
    swing_low = float(df["low"].iloc[-5:].min())
    stop_swing = swing_low - 0.1 * atr
    d = entry - stop_swing
    if d < 1.0 * atr:
        stop, stop_basis = entry - atr, "1× ATR"
    elif d <= 2.0 * atr:
        stop, stop_basis = stop_swing, "below 5-day swing low"
    else:
        stop, stop_basis = entry - 1.5 * atr, "1.5× ATR"
    risk = entry - stop
    risk_pct = risk / entry * 100
    rec.update(entry=entry, stop=stop, stop_basis=stop_basis, risk_pct=risk_pct,
               entry_type="buy above trigger" if primary[2] else "at close / CMP")
    if risk_pct > cfg["max_stop_pct"]:
        return fail(f"stop {risk_pct:.1f}% below entry > {cfg['max_stop_pct']}%")
    ok()

    # 14 target & R:R
    h = df["high"]
    hi252 = float(h.iloc[-253:-1].max())
    levels = [p for p in pivot_highs(h.iloc[-253:-5]) if p > entry * 1.01]
    if hi252 > entry * 1.01:
        levels.append(hi252)
    cap = entry * (1 + cfg["max_target_pct"] / 100)
    if levels:
        res = min(levels)
        target, target_basis = min(res * 0.995, cap), f"just below resistance {res:.2f}"
    else:
        res = None
        target, target_basis = min(entry + 2.5 * risk, cap), "no overhead resistance (2.5R)"
    target_pct = (target / entry - 1) * 100
    rr = (target - entry) / risk
    rec.update(target=target, target_basis=target_basis, target_pct=target_pct, rr=rr,
               nearest_resistance=res)
    if target_pct < cat["min_target_pct"]:
        return fail(f"target only {target_pct:.1f}% away (resistance too close)")
    if rr < cfg["min_rr"]:
        return fail(f"R:R {rr:.2f} < {cfg['min_rr']}")
    ok()

    # 15 position size
    risk_amt = cfg["capital"] * cfg["risk_pct"] / 100
    qty = int(min(risk_amt // risk, cfg["max_position"] // entry))
    pos = qty * entry
    rec.update(qty=qty, position_value=pos, risk_amount=qty * risk)
    if qty < 1:
        return fail("quantity rounds to 0")
    if pos > adtv_cr * 1e7 * cfg["max_pct_of_adtv"] / 100:
        return fail(f"position ₹{pos:,.0f} > {cfg['max_pct_of_adtv']}% of daily traded value")
    ok()

    # ---- passed every hard filter: score for ranking (never rejects) ----
    adx, adx_prev = float(last["adx"]), float(ind["adx"].iloc[-4])
    macd, sig = float(last["macd"]), float(last["macd_signal"])
    hist, hist_prev = float(last["macd_hist"]), float(ind["macd_hist"].iloc[-2])
    rsi_prev = float(ind["rsi"].iloc[-2])
    score, why = 0.0, []
    if rs1 > 0:
        score += 1.5; why.append("1M RS+")
    if family == "breakout":
        if 55 <= rsi <= 75:
            score += 1; why.append("RSI fits breakout")
        if macd > sig:
            score += 1; why.append("MACD>signal")
        if adx >= 20 and adx > adx_prev:
            score += 1; why.append("ADX≥20 rising")
        if not math.isnan(vol_ratio):
            score += min(max(vol_ratio - 1, 0), 1.5); why.append(f"vol {vol_ratio:.1f}x")
    elif family == "pullback":
        if 40 <= rsi <= 60 and rsi > rsi_prev:
            score += 1; why.append("RSI turning up")
        if macd > 0:
            score += 1; why.append("MACD>0")
        if adx >= 20:
            score += 0.5; why.append("trend ADX≥20")
    else:  # consolidation
        if macd >= -0.1 * atr:
            score += 1; why.append("MACD near/above 0")
        if hist > hist_prev:
            score += 1; why.append("MACD hist rising")
    if rr >= 2.5:
        score += 1; why.append(f"R:R {rr:.1f}")
    if stop_basis.startswith("below"):
        score += 0.5; why.append("stop under swing low")
    if C >= 0.95 * hi252:
        score += 0.5; why.append("near 52W high")
    if deliv is not None and deliv >= 50:
        score += 0.5; why.append(f"delivery {deliv:.0f}%")
    rec.update(passed=True, score=round(score, 2), score_notes=why, adx=adx,
               macd_above_signal=bool(macd > sig))
    return rec


def clean_record(rec: dict) -> dict:
    out = {}
    for k, v in rec.items():
        if isinstance(v, (float, np.floating)):
            out[k] = r2(v)
        elif isinstance(v, (np.integer,)):
            out[k] = int(v)
        elif isinstance(v, (np.bool_,)):
            out[k] = bool(v)
        else:
            out[k] = v
    return out


def market_snapshot(nifty: pd.DataFrame, vix: pd.DataFrame | None, breadth: float | None) -> dict:
    ind = compute_indicators(nifty)
    c, last = nifty["close"], ind.iloc[-1]
    h, l = nifty["high"], nifty["low"]
    hh = h.iloc[-20:].max() > h.iloc[-40:-20].max()
    hl = l.iloc[-20:].min() > l.iloc[-40:-20].min()
    snap = {
        "nifty_close": r2(c.iloc[-1]),
        "nifty_ema20": r2(last["ema20"]), "nifty_ema50": r2(last["ema50"]),
        "nifty_ema200": r2(last["ema200"]),
        "nifty_above": {k: bool(c.iloc[-1] > last[k]) for k in ("ema20", "ema50", "ema200")},
        "nifty_ret_5d_pct": r2((c.iloc[-1] / c.iloc[-6] - 1) * 100),
        "nifty_ret_21d_pct": r2((c.iloc[-1] / c.iloc[-22] - 1) * 100),
        "nifty_rsi": r2(last["rsi"]),
        "higher_highs_and_lows_20d": bool(hh and hl),
        "breadth_pct_above_50ema": r2(breadth),
    }
    if vix is not None and len(vix) > 6:
        snap["india_vix"] = r2(vix["close"].iloc[-1])
        snap["india_vix_5d_change_pct"] = r2((vix["close"].iloc[-1] / vix["close"].iloc[-6] - 1) * 100)
    return snap


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------
def run(cfg: dict, constituents: dict, prices: dict, nifty: pd.DataFrame,
        vix: pd.DataFrame | None, bhav: pd.DataFrame | None, surv: dict,
        checks: dict, today: dt.date) -> dict:
    data_date = nifty.index[-1].date()
    base = {"schema_version": SCHEMA_VERSION,
            "generated_at_ist": dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
            "run_date": str(today), "data_date": str(data_date),
            "settings": {k: cfg[k] for k in ("capital", "risk_pct", "max_position",
                                             "max_stop_pct", "max_target_pct", "min_rr")},
            "data_checks": checks}
    if data_date != today:
        base.update(status="no_data_today",
                    message=(f"Latest market data is from {data_date}, not {today}. Either today "
                             "was an exchange holiday or the data had not updated when the scan ran."))
        return base

    bstats = bhav_stats(bhav)
    ctx = {"data_date": data_date, "nifty_close": nifty["close"], "bhav": bstats,
           "bhav_ok": bool(bstats), "surv": surv}

    above50, counted = 0, 0
    categories = {}
    for key, cat in cfg["categories"].items():
        syms = constituents.get(key, [])
        recs = []
        for s in syms:
            df = prices.get(s)
            try:
                rec = evaluate(s, df, cat, cfg, ctx)
            except Exception as e:  # never let one bad series kill the scan
                rec = {"symbol": s, "passed": False, "steps_passed": 0,
                       "failed_step": STEPS[0], "fail_detail": f"error: {e}"}
            recs.append(rec)
            if df is not None and len(df) >= 60 and df.index[-1].date() == data_date:
                counted += 1
                above50 += int(df["close"].iloc[-1] > df["close"].ewm(span=50, adjust=False).mean().iloc[-1])
        funnel = [{"step": "universe", "remaining": len(syms)}]
        for i, name in enumerate(STEPS):
            funnel.append({"step": name, "remaining": sum(1 for r in recs if r["steps_passed"] > i)})
        passed = sorted([r for r in recs if r["passed"]],
                        key=lambda r: (r["score"], r.get("rs_3m_pct", 0)), reverse=True)
        closest = None
        if not passed and recs:
            miss = max(recs, key=lambda r: (r["steps_passed"], r.get("rs_3m_pct") or -999))
            closest = {"symbol": miss["symbol"], "failed_step": miss.get("failed_step"),
                       "detail": miss.get("fail_detail"), "steps_passed": miss["steps_passed"]}
        categories[key] = {
            "label": cat["label"], "universe_size": len(syms),
            "passed_all_hard_filters": len(passed),
            "candidates": [clean_record(r) for r in passed[:cfg["candidates_per_category"]]],
            "closest_miss": closest, "funnel": funnel,
        }

    breadth = above50 / counted * 100 if counted else None
    base.update(status="ok", message="scan complete",
                market=market_snapshot(nifty, vix, breadth), categories=categories)
    return base


def to_markdown(rep: dict) -> str:
    L = [f"# Swing scan — {rep.get('data_date')}",
         f"Status: **{rep['status']}** — {rep.get('message', '')}  ",
         f"Generated {rep.get('generated_at_ist')} IST", ""]
    dc = rep.get("data_checks", {})
    L += ["## Data checks", "```", json.dumps(dc, indent=2, ensure_ascii=False)[:3000], "```", ""]
    if rep["status"] != "ok":
        return "\n".join(L)
    m = rep["market"]
    L += ["## Market", f"Nifty {m['nifty_close']} | 20/50/200 EMA {m['nifty_ema20']} / "
          f"{m['nifty_ema50']} / {m['nifty_ema200']} | 5d {m['nifty_ret_5d_pct']}% | "
          f"21d {m['nifty_ret_21d_pct']}% | VIX {m.get('india_vix')} "
          f"({m.get('india_vix_5d_change_pct')}% 5d) | breadth >50EMA {m['breadth_pct_above_50ema']}%", ""]
    for key, c in rep["categories"].items():
        L.append(f"## {c['label']} — {c['passed_all_hard_filters']} passed of {c['universe_size']}")
        if c["candidates"]:
            L.append("| Symbol | Setup | CMP | Entry | Stop | Target | Qty | R:R | Score | Flags |")
            L.append("|---|---|---|---|---|---|---|---|---|---|")
            for r in c["candidates"]:
                parts = list(r.get("flags", []))
                if r.get("unverified"):
                    parts.append("unverified: " + ", ".join(r["unverified"]))
                fl = " ".join(parts)
                L.append(f"| {r['symbol']} | {r['setup']} | {r['cmp']} | {r['entry']} | {r['stop']} | "
                         f"{r['target']} | {r['qty']} | {r['rr']} | {r['score']} | {fl} |")
        else:
            cm = c["closest_miss"] or {}
            L.append(f"NO TRADE — closest: {cm.get('symbol')} (failed: {cm.get('failed_step')} — {cm.get('detail')})")
        L.append("Funnel: " + " → ".join(f"{f['step']} {f['remaining']}" for f in c["funnel"]))
        L.append("")
    return "\n".join(L)


def write_outputs(rep: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "history").mkdir(exist_ok=True)
    js = json.dumps(rep, indent=2, ensure_ascii=False, default=str)
    (outdir / "latest.json").write_text(js, encoding="utf-8")
    (outdir / "latest.md").write_text(to_markdown(rep), encoding="utf-8")
    (outdir / "history" / f"{rep.get('run_date')}.json").write_text(js, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Daily Indian swing-trade screener")
    ap.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    ap.add_argument("--asof", help="treat this date (YYYY-MM-DD) as today; for re-running a past day")
    ap.add_argument("--no-refresh-lists", action="store_true",
                    help="use the saved index lists instead of downloading them")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    today = dt.date.fromisoformat(args.asof) if args.asof else dt.datetime.now(IST).date()
    checks: dict = {}
    try:
        client = http_client()
        log("index constituents")
        constituents, checks["constituents"] = load_constituents(cfg, client, not args.no_refresh_lists)
        all_syms = sorted({s for v in constituents.values() for s in v})
        if not all_syms:
            raise RuntimeError("no constituent lists available — add CSVs to data/constituents/")

        log(f"prices for {len(all_syms)} stocks + Nifty + VIX")
        frames = fetch_prices([NIFTY_TICKER, VIX_TICKER], cfg["history_period"], chunk=2, pause=1)
        nifty, vix = frames.get(NIFTY_TICKER), frames.get(VIX_TICKER)
        if nifty is None:
            raise RuntimeError("could not download Nifty 50 index data from Yahoo")
        ticker_map = {f"{s}.NS": s for s in all_syms}
        raw = fetch_prices(list(ticker_map), cfg["history_period"])
        prices = {ticker_map[t]: df for t, df in raw.items()}
        if args.asof:
            cut = pd.Timestamp(today)
            nifty = nifty[nifty.index <= cut]
            vix = vix[vix.index <= cut] if vix is not None else None
            prices = {s: d[d.index <= cut] for s, d in prices.items()}
        missing = sorted(set(all_syms) - set(prices))
        checks["prices"] = {"source": "Yahoo Finance (yfinance)", "requested": len(all_syms),
                            "received": len(prices), "missing": missing[:60]}

        bhav, surv = None, {"asm": None, "gsm": None, "esm": None, "fo_ban": None, "errors": {}}
        if nifty.index[-1].date() == today:
            dates = [d.date() for d in nifty.index[-22:]]
            log("NSE bhavcopies (delivery %, series, turnover)")
            bhav, bfails = fetch_bhavcopies(client, dates)
            n_ok = 0 if bhav is None else bhav["DATE"].nunique()
            checks["nse_bhavcopy"] = {"days_ok": int(n_ok), "days_requested": len(dates),
                                      "failures": bfails[:5]}
            if not args.asof:
                log("NSE surveillance lists")
                surv = fetch_surveillance(client)
        checks["surveillance"] = {k: ("ok" if surv.get(k) is not None else "UNVERIFIED")
                                  for k in ("asm", "gsm", "esm", "fo_ban")}
        if surv.get("errors"):
            checks["surveillance"]["errors"] = surv["errors"]

        rep = run(cfg, constituents, prices, nifty, vix, bhav, surv, checks, today)
        write_outputs(rep, args.out)
        log(f"done: {rep['status']} — {rep.get('message')}")
        return 0
    except Exception as e:
        rep = {"schema_version": SCHEMA_VERSION, "status": "error",
               "generated_at_ist": dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
               "run_date": str(today), "data_date": None,
               "message": f"{type(e).__name__}: {e}", "data_checks": checks,
               "traceback": traceback.format_exc()[-2000:]}
        write_outputs(rep, args.out)
        log(f"FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
