# views.py
import logging

from celery import Celery
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .tasks import predict_and_store
from StockApp.models import PredictedStockData
from StockApp.serializers import PredictedStockDataSerializer
logger = logging.getLogger(__name__)

CACHE_TIMEOUT_MINUTES = 5 * 60
app = Celery("Stock")








@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def predict_stock_prices_api(request, symbol):
    symbol=symbol.upper()
    try:
        period = request.query_params.get("period", 30)  #
        period = int(period)

        # Call the prediction function
        forecast = predict_and_store(symbol)
        
        return Response({
            "symbol": symbol,
            "forecast": forecast
        }, status=status.HTTP_200_OK)
    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"Failed to predict prices: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnonRateThrottle])
def get_predicted_data(request, symbol):

    try:
        # Fetch predicted data for the given symbol
        predictions = PredictedStockData.objects.filter(symbol=symbol).order_by('-timestamp')
        
        # Serialize the data
        serializer = PredictedStockDataSerializer(predictions, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)