import logging
from celery import Celery
from celery.exceptions import CeleryError, TimeoutError
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .tasks import fetch_stock_data_from_alpha_api
from StockApp.models import StockHistoryData
from StockApp.serializers import StockHistoryDataSerializer

logger = logging.getLogger(__name__)

CACHE_TIMEOUT_MINUTES = 5 * 60
app = Celery("Stock")

# Constants for error messages
ERROR_SYMBOL_REQUIRED = "Symbol is required and must be a string."
ERROR_CELERY_TASK_START = "Error starting the celery task."
ERROR_UNEXPECTED = "An unexpected error occurred."
ERROR_SYMBOL_STRING = "Symbol must be a string."
MESSAGE_DATA_PROCESSING = "Data fetching for {} is now being processed in the background."

def validate_symbol(symbol):

    if not symbol or not isinstance(symbol, str):
        return False
    return symbol.upper()

def handle_celery_task(result, symbol):
    try:
        task_response = result.get(timeout=10)
        print("task_response", task_response)
        if isinstance(task_response, dict) and "error" in task_response:
            error_message = task_response["error"]
            if error_message:
                return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(task_response)
    except TimeoutError:
        return Response({"message": MESSAGE_DATA_PROCESSING.format(symbol)}, status=status.HTTP_202_ACCEPTED)
    except CeleryError as e:
        logger.error(f"Celery task error: {str(e)}")
        return Response({"error": ERROR_CELERY_TASK_START}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@throttle_classes([AnonRateThrottle])
def get_stock_history_data(request):
    symbol = validate_symbol(request.data.get("symbol"))
    
    if not symbol:
        return Response({"error": ERROR_SYMBOL_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

    try:
        
        result = fetch_stock_data_from_alpha_api.delay(symbol)
        # print("symbol", symbol)
        return handle_celery_task(result, symbol)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response({"error": ERROR_UNEXPECTED}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@cache_page(CACHE_TIMEOUT_MINUTES)
@throttle_classes([AnonRateThrottle])
def get_all_stock_data(request):
    try:
        stock_data = StockHistoryData.objects.all()
        serializer = StockHistoryDataSerializer(stock_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error fetching all stock data: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@cache_page(CACHE_TIMEOUT_MINUTES)
@throttle_classes([AnonRateThrottle])
def get_stock_data_by_symbol_api(request, symbol):
    symbol = validate_symbol(symbol)
    if not symbol:
        return Response({"error": ERROR_SYMBOL_STRING}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stock_data = list(StockHistoryData.objects.filter(symbol=symbol))
        if stock_data:
            serializer = StockHistoryDataSerializer(stock_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "Stock data not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching stock data by symbol: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
