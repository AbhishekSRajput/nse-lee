#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from datetime import date, datetime

from nse.client import NSESession
from nse.bhavcopy import get_delivery_data
from nse.fii_dii import get_fii_dii
from nse.fo_ban import get_fo_ban_list
from nse.indices import get_sector_performance
from nse.corporate_actions import get_corporate_actions, get_earnings_tickers
from nse.option_chain import get_batch_pcr

ALL_MODULES = ["delivery", "fii", "indices", "fo_ban", "corporate", "options"]

DEFAULT_PCR_TICKERS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "LT",
    "BAJFINANCE", "MARUTI", "TATAMOTORS", "AXISBANK", "WIPRO",
    "SUNPHARMA", "TATASTEEL", "POWERGRID", "NTPC", "ADANIENT",
]

logger = logging.getLogger("nse")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch daily NSE market data and save as JSON"
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=ALL_MODULES,
        default=None,
        help="Fetch only specific modules (default: all)",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated tickers for option chain PCR (e.g. TCS,INFY,RELIANCE)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Specific date for delivery data (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./data",
        help="Output directory (default: ./data)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def should_run(module, only_modules):
    if only_modules is None:
        return True
    return module in only_modules


def main():
    args = parse_args()
    setup_logging(args.verbose)

    modules = args.only
    pcr_tickers = args.tickers.split(",") if args.tickers else DEFAULT_PCR_TICKERS
    pcr_tickers = [t.strip().upper() for t in pcr_tickers]

    for_date = None
    if args.date:
        try:
            for_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    result = {
        "date": date.today().isoformat(),
        "generated_at": datetime.now().astimezone().isoformat(),
    }

    try:
        session = NSESession()
        print("✓ NSE session established")
    except Exception as exc:
        logger.error("Failed to establish NSE session: %s", exc)
        print(f"✗ Session failed: {exc}")
        sys.exit(1)

    # --- Delivery data ---
    if should_run("delivery", modules):
        try:
            delivery = get_delivery_data(session, for_date=for_date)
            result["delivery"] = delivery
            print(f"✓ Delivery: {len(delivery)} stocks")
        except Exception as exc:
            logger.error("Delivery fetch failed: %s", exc)
            print(f"✗ Delivery failed: {exc}")
            result["delivery"] = {}

    # --- FII/DII ---
    if should_run("fii", modules):
        try:
            fii_dii = get_fii_dii(session)
            result["fii_dii"] = fii_dii
            if fii_dii:
                print(
                    f"✓ FII/DII: FII {fii_dii['fii_signal']} "
                    f"({fii_dii['fii_net_cr']:+.0f} Cr), "
                    f"DII {fii_dii['dii_signal']} "
                    f"({fii_dii['dii_net_cr']:+.0f} Cr)"
                )
            else:
                print("⚠ FII/DII: no data returned")
        except Exception as exc:
            logger.error("FII/DII fetch failed: %s", exc)
            print(f"✗ FII/DII failed: {exc}")
            result["fii_dii"] = None

    # --- F&O Ban ---
    if should_run("fo_ban", modules):
        try:
            fo_ban = get_fo_ban_list(session)
            result["fo_ban"] = fo_ban
            print(f"✓ F&O Ban: {len(fo_ban)} stocks")
        except Exception as exc:
            logger.error("F&O ban fetch failed: %s", exc)
            print(f"✗ F&O Ban failed: {exc}")
            result["fo_ban"] = []

    # --- Sector Indices ---
    if should_run("indices", modules):
        try:
            sectors = get_sector_performance(session)
            result["sector_indices"] = sectors
            print(f"✓ Sector indices: {len(sectors)} indices")
        except Exception as exc:
            logger.error("Sector indices fetch failed: %s", exc)
            print(f"✗ Sector indices failed: {exc}")
            result["sector_indices"] = {}

    # --- Corporate Actions ---
    if should_run("corporate", modules):
        try:
            actions = get_corporate_actions(session)
            result["corporate_actions"] = actions

            earnings_blackout = sorted(get_earnings_tickers(actions))
            result["earnings_blackout"] = earnings_blackout

            print(
                f"✓ Corporate actions: {len(actions)} events, "
                f"{len(earnings_blackout)} earnings blackout"
            )
        except Exception as exc:
            logger.error("Corporate actions fetch failed: %s", exc)
            print(f"✗ Corporate actions failed: {exc}")
            result["corporate_actions"] = []
            result["earnings_blackout"] = []

    # --- Option Chains ---
    if should_run("options", modules):
        try:
            option_chains = get_batch_pcr(session, pcr_tickers)
            result["option_chains"] = option_chains
            print(f"✓ Option chains: {len(option_chains)} stocks")
        except Exception as exc:
            logger.error("Option chain fetch failed: %s", exc)
            print(f"✗ Option chains failed: {exc}")
            result["option_chains"] = {}

    # --- Save output ---
    today_str = date.today().isoformat()
    latest_path = os.path.join(output_dir, "nse-latest.json")
    dated_path = os.path.join(output_dir, f"nse-{today_str}.json")

    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    with open(dated_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    print(f"\nSaved: {dated_path}")
    print(f"Saved: {latest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
