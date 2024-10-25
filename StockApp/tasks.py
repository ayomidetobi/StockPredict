# tasks.py
import os
from datetime import datetime, timedelta
from prophet import Prophet
import requests
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from decouple import config
# from .backtesttasks import BackTestingUseCase
# from .views import get_stock_data_by_symbol
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from .models import StockHistoryData,PredictedStockData
from .predicted import prepare_data_for_prophet,predict_all_data,store_predictions

API_KEY = config("API_KEY")
BASE_URL = config("BASE_URL")


def save_stock_data(symbol, time_series, two_years_ago_timestamp):
    for date, values in time_series.items():
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_timestamp = int(date_obj.timestamp())
            if date_timestamp >= two_years_ago_timestamp:
                stock_data = StockHistoryData(
                    symbol=symbol,
                    timestamp=date_timestamp,
                    open_price=values.get("1. open"),
                    high_price=values.get("2. high"),
                    low_price=values.get("3. low"),
                    close_price=values.get("4. close"),
                    volume=values.get("5. volume"),
                )
                stock_data.save()
        except IntegrityError:
            error_message = f"Error saving data for {symbol}: UNIQUE constraint failed."
            return error_message
        except Exception as e:
            print(f"Error saving data for {symbol} : {str(e)}")


@shared_task(bind=True)
def fetch_stock_data_from_alpha_api(self, symbol):
    try:
        url = f"{BASE_URL}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            two_years_ago = timezone.now() - timedelta(days=2 * 365)
            two_years_ago_timestamp = int(two_years_ago.timestamp())

            result = save_stock_data(symbol, time_series, two_years_ago_timestamp)
            if result and "Error" in result:
                return result
            return f"Data for {symbol} stored successfully."
        if "Information" in data:
            return {
                "error": "Alpha Vantage API Rate Limit Reached",
            }
        else:
            error_message = data.get("Note", "Invalid API response")
            return f"Error fetching data for {symbol}: {error_message}"
    except requests.RequestException as e:
        return f"Error fetching data from Alpha API: {str(e)}"
    except SoftTimeLimitExceeded:
        return "Task was terminated due to time limit exceeded."
    except ConnectionError:
        return "connection error: Unable to connect to the Redis server. Please check Redis connection settings."
    except PermissionError:
        return "Permission denied: Unable to write to the Redis server."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"




@shared_task
def predict_and_store_stock_prices(symbol, period=30):
    try:
        predictions = predict_all_data(symbol, period)
        store_predictions(symbol, predictions)
        return predictions
    except Exception as e:
        print(f"Error predicting stock prices for {symbol}: {e}")
        raise e
