
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.coingecko.com/api/v3"
API_KEY = os.getenv("COINGECKO_API_KEY")

HEADERS = {}
if API_KEY:
    HEADERS["x-cg-demo-api-key"] = API_KEY


class CryptoAPIError(Exception):
    """Raised when a cryptocurrency API request fails."""


def fetch_market_data(limit=10, currency="usd"):
    """Fetch cryptocurrencies ranked by market capitalization."""
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    params = {
        "vs_currency": currency.lower(),
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    try:
        response = requests.get(
            f"{BASE_URL}/coins/markets",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            raise CryptoAPIError("Unexpected API response.")

        return data

    except requests.RequestException as exc:
        raise CryptoAPIError(
            f"Could not retrieve market data: {exc}"
        ) from exc


def fetch_coin_price(coin_id, currency="usd"):
    """Fetch a coin's current price and 24-hour change."""
    coin_id = coin_id.lower()
    currency = currency.lower()

    params = {
        "ids": coin_id,
        "vs_currencies": currency,
        "include_24hr_change": "true",
    }

    try:
        response = requests.get(
            f"{BASE_URL}/simple/price",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        raise CryptoAPIError(
            f"Could not retrieve price: {exc}"
        ) from exc

    coin = data.get(coin_id)

    if not coin or currency not in coin:
        raise CryptoAPIError(
            f"Coin '{coin_id}' was not found. "
            "Try an ID such as bitcoin, ethereum, or solana."
        )

    return {
        "id": coin_id,
        "price": coin[currency],
        "change_24h": coin.get(
            f"{currency}_24h_change"
        ),
    }


def format_price(price, currency="USD"):
    """Format a cryptocurrency price."""
    currency = currency.upper()

    if price >= 1:
        return f"{currency} {price:,.2f}"

    return f"{currency} {price:.8f}".rstrip("0").rstrip(".")


def format_market_cap(value):
    """Format market capitalization in a readable form."""
    if value is None:
        return "N/A"

    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    return f"${value:,.0f}"
