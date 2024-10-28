from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .tasks import predict_and_store
from StockApp.models import PredictedStockData
from StockApp.serializers import PredictedStockDataSerializer
from StockApp.utils import StandardResultsSetPagination


class StockPredictionView(APIView):
    throttle_classes = [AnonRateThrottle]

    def get(self, request, symbol):
        symbol = symbol.upper()
        try:
            period = int(request.query_params.get("period", 30))
            forecast = predict_and_store(symbol)
            return Response({"symbol": symbol, "forecast": forecast}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": f"{symbol} is not a valid input"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Internal server error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictedDataView(APIView):
    throttle_classes = [AnonRateThrottle]

    # pagination_class = StandardResultsSetPagination
    def get(self, request, symbol):
        try:
            predictions = PredictedStockData.objects.filter(symbol=symbol.upper()).order_by("-timestamp")

            serializer = PredictedStockDataSerializer(predictions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PredictedStockData.DoesNotExist:
            return Response({"error": "No predictions found for this symbol"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve predictions {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
