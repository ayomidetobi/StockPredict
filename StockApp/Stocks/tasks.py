# tasks.py
from datetime import datetime, timedelta
import logging
import requests
from celery import shared_task
from decouple import config
from django.db import IntegrityError
from django.utils import timezone

from StockApp.models import StockHistoryData
logger = logging.getLogger(__name__)
API_KEY = config("API_KEY")
BASE_URL = config("BASE_URL")

DATE_FORMAT = "%Y-%m-%d"
STOCK_KEYS = {
    "open": "1. open",
    "high": "2. high",
    "low": "3. low",
    "close": "4. close",
    "volume": "5. volume",
}


def parse_date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)


def convert_to_timestamp(date_str):
    return int(parse_date(date_str).timestamp())


def is_within_time_range(timestamp, cutoff_timestamp):
    return timestamp >= cutoff_timestamp


def parse_price(value):
    return float(value)


def parse_volume(value):
    return int(value)


def create_stock_history_data(symbol, timestamp, daily_data):
    try:
        StockHistoryData.objects.create(
            symbol=symbol,
            timestamp=timestamp,
            open_price=parse_price(daily_data[STOCK_KEYS["open"]]),
            high_price=parse_price(daily_data[STOCK_KEYS["high"]]),
            low_price=parse_price(daily_data[STOCK_KEYS["low"]]),
            close_price=parse_price(daily_data[STOCK_KEYS["close"]]),
            volume=parse_volume(daily_data[STOCK_KEYS["volume"]]),
        )
        return None
    except IntegrityError:
        return f"Error saving data for {symbol}: UNIQUE constraint failed."


def save_stock_data(symbol, time_series, cutoff_timestamp):
    for date_str, daily_data in time_series.items():
        timestamp = convert_to_timestamp(date_str)

        if is_within_time_range(timestamp, cutoff_timestamp):
            error = create_stock_history_data(symbol, timestamp, daily_data)
            if error:
                return error

    return None


@shared_task(bind=True)
def fetch_stock_data_from_alpha_api(self, symbol):
    symbol.upper()
    logger.info(f"Fetching stock data for symbol: {symbol}")
    try:
        url = f"{BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={API_KEY}"
        print("url", url)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            two_years_ago = timezone.now() - timedelta(days=2 * 365)
            two_years_ago_timestamp = int(two_years_ago.timestamp())

            result = save_stock_data(symbol, time_series, two_years_ago_timestamp)
            if result and "Error" in result:
                logger.error(f"Failed to save data: {result}")
                return {"status_code": 409, "error": result}
            return {"status_code": 200, "message": f"Data for {symbol} stored successfully."}
        if "Information" in data:
            logger.warning("API rate limit reached")
            return {"status_code": 429, "error": "Alpha Vantage API Rate Limit Reached"}
        else:
            error_message = data.get("Note", "Invalid API response")
            logger.error(f"API error for {symbol}: {error_message}")
            return {
                "status_code": 400,
                "error": f"Error fetching data for {symbol}: {error_message}",
            }
    except requests.RequestException as e:
        logger.exception(f"Request failed for {symbol}")
        return {"status_code": 500, "error": f"Error fetching data for {symbol}: {str(e)}"}
