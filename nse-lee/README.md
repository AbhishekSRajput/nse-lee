# nse-lee

Python library that fetches live market data from NSE (National Stock Exchange of India) official endpoints. Part of the NSE swing trading system — runs standalone and saves JSON output that a Next.js dashboard reads.

## Setup

```bash
cd nse-lee
pip install -r requirements.txt
```

## Usage

```bash
# Full fetch (all modules)
python fetch_daily.py

# Specific modules only
python fetch_daily.py --only delivery fii indices

# Custom tickers for option chain PCR
python fetch_daily.py --tickers TCS,INFY,RELIANCE

# Specific date (delivery data only)
python fetch_daily.py --date 2024-03-20

# Custom output directory
python fetch_daily.py --output ./data

# Debug logging
python fetch_daily.py --verbose
```

## Output

Saves two files:
- `data/nse-latest.json` — always overwritten
- `data/nse-YYYY-MM-DD.json` — date-stamped archive

## Modules

| Module | Data | Source |
|---|---|---|
| `bhavcopy` | Delivery % for all stocks | MTO archive file |
| `fii_dii` | FII/DII net flows in ₹ Cr | `/api/fiidiiTradeReact` |
| `fo_ban` | F&O ban list | `/api/fo-banlist` |
| `indices` | Sector index performance + VIX | `/api/equity-stockIndices` |
| `corporate_actions` | Earnings calendar, dividends, splits | `/api/corporates-corporateActions` |
| `option_chain` | PCR, max pain, OI per stock | `/api/option-chain-equities` |

## Testing

```bash
# Unit tests (no HTTP)
pytest tests/ -v -m "not integration"

# Integration tests (hits real NSE)
pytest tests/ -v -m integration
```
