import pytest
import responses
from unittest.mock import patch, MagicMock

from nse.client import NSESession, BASE_URL


SAMPLE_MTO_DATA = """\
20|1|RELIANCE|EQ|1234567|891234|72.20
20|2|TCS|EQ|456789|312000|68.40
20|3|INFY|EQ|789012|500000|63.37
20|4|SBIN|FUT|100000|50000|50.00
20|5|HDFCBANK|EQ|654321|450000|68.78
20|6|BADSTOCK|EQ|1000|1500|150.00
"""

SAMPLE_FII_DII = [
    {
        "category": "FII/FPI",
        "buyValue": "12,345.67",
        "sellValue": "10,234.56",
        "netValue": "2,111.11",
    },
    {
        "category": "DII",
        "buyValue": "8,765.43",
        "sellValue": "9,876.54",
        "netValue": "-1,111.11",
    },
]

SAMPLE_FII_DII_SELLING = [
    {
        "category": "FII/FPI",
        "buyValue": "5,000.00",
        "sellValue": "8,500.00",
        "netValue": "-3,500.00",
    },
    {
        "category": "DII",
        "buyValue": "9,000.00",
        "sellValue": "7,500.00",
        "netValue": "1,500.00",
    },
]

SAMPLE_FO_BAN = {
    "data": [
        {"tradingSymbol": "NALCO"},
        {"tradingSymbol": "IBULHSGFIN"},
        {"tradingSymbol": "HINDCOPPER"},
    ]
}

SAMPLE_FO_BAN_EMPTY = {"data": []}

SAMPLE_INDEX = {
    "data": [
        {
            "symbol": "NIFTY BANK",
            "last": 48234.55,
            "pChange": 1.23,
            "advances": 8,
            "declines": 4,
        },
        {"symbol": "HDFCBANK", "last": 1600.0, "pChange": 0.5},
    ]
}

SAMPLE_VIX_INDEX = {
    "data": [
        {
            "symbol": "INDIA VIX",
            "last": 12.5,
            "pChange": -2.1,
        }
    ]
}

SAMPLE_CORPORATE_ACTIONS = [
    {
        "symbol": "TCS",
        "purpose": "Quarterly Results/Financial Results",
        "exDate": "25-Mar-2024",
    },
    {
        "symbol": "INFY",
        "purpose": "Board Meeting - Annual Result",
        "exDate": "28-03-2024",
    },
    {
        "symbol": "RELIANCE",
        "purpose": "Interim Dividend - Rs 5 Per Share",
        "exDate": "15-Apr-2024",
    },
    {
        "symbol": "ITC",
        "purpose": "Bonus Issue 1:1",
        "exDate": "20-Apr-2024",
    },
    {
        "symbol": "WIPRO",
        "purpose": "Stock Split from Rs 10 to Rs 2",
        "exDate": "10-Apr-2024",
    },
    {
        "symbol": "HDFCBANK",
        "purpose": "Buy Back of Shares",
        "exDate": "05-Apr-2024",
    },
]

SAMPLE_OPTION_CHAIN = {
    "records": {
        "expiryDates": ["28-Mar-2024", "25-Apr-2024"],
        "data": [
            {
                "strikePrice": 2800,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 5000},
                "PE": {"openInterest": 3000},
            },
            {
                "strikePrice": 2850,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 8000},
                "PE": {"openInterest": 6000},
            },
            {
                "strikePrice": 2900,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 3000},
                "PE": {"openInterest": 10000},
            },
            {
                "strikePrice": 2800,
                "expiryDate": "25-Apr-2024",
                "CE": {"openInterest": 1000},
                "PE": {"openInterest": 1000},
            },
        ],
    }
}

SAMPLE_OPTION_CHAIN_BULLISH = {
    "records": {
        "expiryDates": ["28-Mar-2024"],
        "data": [
            {
                "strikePrice": 100,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 10000},
                "PE": {"openInterest": 3000},
            },
            {
                "strikePrice": 110,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 10000},
                "PE": {"openInterest": 3000},
            },
        ],
    }
}

SAMPLE_OPTION_CHAIN_BEARISH = {
    "records": {
        "expiryDates": ["28-Mar-2024"],
        "data": [
            {
                "strikePrice": 100,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 1000},
                "PE": {"openInterest": 5000},
            },
            {
                "strikePrice": 110,
                "expiryDate": "28-Mar-2024",
                "CE": {"openInterest": 1000},
                "PE": {"openInterest": 5000},
            },
        ],
    }
}


@pytest.fixture
def nse_session():
    with patch.object(NSESession, "refresh", return_value=None):
        session = NSESession()
        session._last_refresh = 9999999999.0
        yield session
