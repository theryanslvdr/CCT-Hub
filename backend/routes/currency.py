"""Currency exchange rate routes."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import httpx
import os
import logging

from deps import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/currency", tags=["Currency"])

# Cache for USDT rates
_usdt_rates_cache = {
    "data": None,
    "timestamp": None,
    "fetching": False,
}


async def get_usdt_rates():
    """Get USDT exchange rates from CoinGecko API with caching (15 min cache)"""
    global _usdt_rates_cache

    if _usdt_rates_cache["data"] and _usdt_rates_cache["timestamp"]:
        cache_age = (datetime.now(timezone.utc) - _usdt_rates_cache["timestamp"]).total_seconds()
        if cache_age < 900:
            return _usdt_rates_cache["data"]

    if _usdt_rates_cache["fetching"]:
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]
        import asyncio
        await asyncio.sleep(0.5)
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]

    try:
        _usdt_rates_cache["fetching"] = True
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "tether",
                    "vs_currencies": "usd,php,eur,gbp,jpy,cny,krw,sgd,hkd,aud,cad,inr,myr,thb,idr,vnd"
                },
                timeout=10.0,
                headers={"Accept": "application/json"},
            )

            if response.status_code == 429:
                logger.warning("CoinGecko rate limited, using cache or fallback")
                if _usdt_rates_cache["data"]:
                    return _usdt_rates_cache["data"]
                raise Exception("Rate limited")

            data = response.json()
            if "tether" in data:
                tether_prices = data["tether"]
                rates = {currency.upper(): price for currency, price in tether_prices.items()}
                rates["USDT"] = 1

                result = {
                    "base": "USDT",
                    "rates": rates,
                    "source": "coingecko",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                _usdt_rates_cache["data"] = result
                _usdt_rates_cache["timestamp"] = datetime.now(timezone.utc)
                _usdt_rates_cache["fetching"] = False
                return result
            else:
                raise Exception("Invalid CoinGecko response")
    except Exception as e:
        _usdt_rates_cache["fetching"] = False
        logger.error(f"CoinGecko USDT API error: {e}")
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]

        return {
            "base": "USDT",
            "rates": {
                "USD": 1.0, "PHP": 58.0, "EUR": 0.92, "GBP": 0.79,
                "JPY": 149.5, "CNY": 7.25, "KRW": 1350, "SGD": 1.35,
                "HKD": 7.82, "AUD": 1.55, "CAD": 1.36, "INR": 83.5,
                "MYR": 4.72, "THB": 35.8, "IDR": 15750, "VND": 24500,
                "USDT": 1,
            },
            "source": "fallback",
        }


@router.get("/rates")
async def get_exchange_rates(base: str = "USD"):
    try:
        api_key = os.environ.get('EXCHANGE_RATE_API_KEY', '')

        if base.upper() == "USDT":
            return await get_usdt_rates()

        if not api_key:
            return {
                "base": base,
                "rates": {"USD": 1, "PHP": 56.5, "USDT": 1, "EUR": 0.92, "GBP": 0.79},
                "source": "mock",
            }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}",
                timeout=10.0,
            )
            data = response.json()
            return {
                "base": base,
                "rates": data.get("conversion_rates", {}),
                "source": "exchangerate-api",
            }
    except Exception as e:
        logger.error(f"Currency API error: {e}")
        return {
            "base": base,
            "rates": {"USD": 1, "PHP": 56.5, "USDT": 1},
            "source": "fallback",
        }


@router.post("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    rates_data = await get_exchange_rates(from_currency)
    rates = rates_data.get("rates", {})

    if to_currency not in rates:
        raise HTTPException(status_code=400, detail=f"Currency {to_currency} not supported")

    converted = amount * rates[to_currency]
    return {
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "converted": round(converted, 2),
        "rate": rates[to_currency],
    }
