from .models import StockHistoryData
from datetime import datetime
from rest_framework.pagination import PageNumberPagination


def validate_symbol(symbol):
    if not symbol or not isinstance(symbol, str):
        return False
    return symbol.upper()


def get_all_data_by_symbol(symbol):
    validated_symbol = validate_symbol(symbol)
    if not validated_symbol:
        raise ValueError("Invalid symbol provided.")
    symbol = symbol.upper()
    try:
        stock_data = StockHistoryData.objects.filter(symbol=symbol).order_by("timestamp")
        return stock_data
    except Exception as e:
        print(f"Failed to retrieve data for {symbol}: {e}")
        raise e


def get_closing_prices_by_symbol(symbol):
    validated_symbol = validate_symbol(symbol)
    if not validated_symbol:
        raise ValueError("Invalid symbol provided.")
    symbol = symbol.upper()
    try:
        stock_data = (
            StockHistoryData.objects.filter(symbol=validated_symbol)
            .order_by("-timestamp")
            .values_list("close_price", flat=True)
        )
        closing_prices = [float(close_price) for close_price in stock_data]
        return closing_prices
    except Exception as e:
        print(f"Failed to retrieve data for {symbol}: {e}")


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
