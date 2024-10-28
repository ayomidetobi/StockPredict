import logging
from celery import Celery
from celery.exceptions import CeleryError, TimeoutError
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from .tasks import fetch_stock_data_from_alpha_api
from StockApp.models import StockHistoryData
from StockApp.serializers import StockHistoryDataSerializer
from StockApp.utils import StandardResultsSetPagination

logger = logging.getLogger(__name__)
CACHE_TIMEOUT_MINUTES = 5 * 60
app = Celery("Stock")

ERROR_SYMBOL_REQUIRED = "Symbol is required and must be a string."
ERROR_CELERY_TASK_START = "Error starting the celery task."
ERROR_UNEXPECTED = "An unexpected error occurred."
ERROR_SYMBOL_STRING = "Symbol must be a string."
MESSAGE_DATA_PROCESSING = "Data fetching for {} is now being processed in the background."


class BaseStockView(APIView):
    throttle_classes = [AnonRateThrottle]

    def validate_symbol(self, symbol):
        if not symbol or not isinstance(symbol, str):
            return False
        return symbol.upper()

    def handle_celery_task(self, result, symbol):
        try:
            task_response = result.get(timeout=5)
            if isinstance(task_response, dict):
                if "error" in task_response:
                    error_message = task_response["error"]
                    status_code = task_response.get("status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
                    return Response({"error": error_message}, status=status_code)
                elif "message" in task_response:
                    status_code = task_response.get("status_code", status.HTTP_200_OK)
                    return Response({"message": task_response["message"]}, status=status_code)

        except TimeoutError:
            return Response(
                {"message": MESSAGE_DATA_PROCESSING.format(symbol), "task_id": result.task_id},
                status=status.HTTP_202_ACCEPTED,
            )
        except CeleryError as e:
            logger.error(f"Celery task error: {str(e)}")
            return Response({"error": ERROR_CELERY_TASK_START}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error in celery task for symbol {symbol}: {str(e)}")
            return Response({"error": ERROR_UNEXPECTED}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockHistoryDataView(BaseStockView):
    def post(self, request):
        symbol = self.validate_symbol(request.data.get("symbol"))

        if not symbol:
            return Response({"error": ERROR_SYMBOL_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = fetch_stock_data_from_alpha_api.delay(symbol)
            return self.handle_celery_task(result, symbol)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": ERROR_UNEXPECTED}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(cache_page(CACHE_TIMEOUT_MINUTES), name="get")
class AllStockDataView(BaseStockView):
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            stock_data = StockHistoryData.objects.all()
            serializer = StockHistoryDataSerializer(stock_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching all stock data: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(cache_page(CACHE_TIMEOUT_MINUTES), name="get")
class StockDataBySymbolView(BaseStockView):
    def get(self, request, symbol):
        symbol = self.validate_symbol(symbol)
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
