import logging

from celery import Celery
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .tasks import backtest_strategy
from StockApp.serializers import BacktestSerializer
from StockApp.utils import get_closing_prices_by_symbol, validate_symbol
logger = logging.getLogger(__name__)

CACHE_TIMEOUT_MINUTES = 5 * 60
app = Celery("Stock")


@throttle_classes([AnonRateThrottle])
class BacktestView(APIView):
    def validate_backtest_input(self, data):
        required_fields = ['initial_investment', 'short_moving_average', 'long_moving_average', 'symbol']
        for field in required_fields:
            if field not in data or not data[field]:
                return Response({"error": f"{field} is required and cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(data['symbol'], str):
            return Response({"error": "symbol must be a string"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(data['short_moving_average'], int) or not isinstance(data['long_moving_average'], int):
            return Response({"error": "moving averages must be integers"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(data['initial_investment'], (int, float)):
            return Response({"error": "initial_investment must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        
        return None
    def post(self, request):
        serializer = BacktestSerializer(data=request.data)
        validation_result = self.validate_backtest_input(request.data)
        if isinstance(validation_result, Response):
            return validation_result
        if serializer.is_valid():
            initial_investment = serializer.validated_data["initial_investment"]
            
            short_moving_average = serializer.validated_data["short_moving_average"]
            long_moving_average = serializer.validated_data["long_moving_average"]
            symbol = validate_symbol(serializer.validated_data["symbol"])
            stock_prices = get_closing_prices_by_symbol(symbol)
            print("stock_prices", stock_prices)
            results = backtest_strategy(
                stock_prices, short_moving_average, long_moving_average, initial_investment,symbol
            )

            return Response({"results": results}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)