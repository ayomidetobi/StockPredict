# views.py
import logging

from celery import Celery
from celery.exceptions import CeleryError, TimeoutError
from django.http import FileResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .backtesttasks import backtest_strategy
from .models import StockHistoryData
from .serializers import BacktestSerializer, StockHistoryDataSerializer
from .tasks import fetch_stock_data_from_alpha_api
from .utils import get_closing_prices_by_symbol
from .tasks import predict_and_store_stock_prices
from .models import PredictedStockData
from .serializers import PredictedStockDataSerializer
logger = logging.getLogger(__name__)

CACHE_TIMEOUT_MINUTES = 5 * 60
app = Celery("Stock")






from django.http import HttpResponse
from .utils import generate_backtest_insights, generate_prediction_graph, create_pdf_report, generate_pdf_report
PDF_SAVE_PATH ="reports/"
import os
@throttle_classes([AnonRateThrottle])
class GenerateBacktestReportView(APIView):
    def post(self, request, *args, **kwargs):
   
        backtest_data = request.data.get("results", {})

        # Generate images
        insights_img = generate_backtest_insights(backtest_data)# Example messages data

        # Create PDF
        pdf_buffer = generate_pdf_report(
            backtest_data,
            graph_image=insights_img  # Optional if you want to pass insights image
        )
        if not os.path.exists(PDF_SAVE_PATH):
            os.makedirs(PDF_SAVE_PATH)
        pdf_filename = "backtest_report.pdf"  # Or use a more dynamic name
        pdf_path = os.path.join(PDF_SAVE_PATH, pdf_filename)
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf_buffer.getvalue())
        # Create HTTP response with PDF
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="backtest_report.pdf"'
        return response

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from .utils import generate_prediction_graph, create_pdf_report
from .models import StockHistoryData
from datetime import datetime, timedelta

class GeneratePredictionReportView(APIView):
    throttle_classes = [AnonRateThrottle]

    def get_historical_data(self, symbol):

        try:
            # Calculate the timestamp for 30 days ago from now
            date_30_days_ago = datetime.now() - timedelta(days=30)
            timestamp_30_days_ago = int(date_30_days_ago.timestamp())

            # Query to get stock data from the past 30 days
            historical_data = StockHistoryData.objects.filter(
                symbol=symbol.upper(), 
                timestamp__gte=timestamp_30_days_ago  # Assuming 'date' is stored as a Unix timestamp (int)
            ).order_by('timestamp')

            # Convert the timestamp to a human-readable date string
            return [{"timestamp": datetime.fromtimestamp(data.timestamp).strftime('%Y-%m-%d'), "price": data.close_price} for data in historical_data]
        except Exception as e:
            print(f"Failed to retrieve historical data for symbol {symbol}: {e}")
            raise e

    def post(self, request, *args, **kwargs):
        # Get symbol from request data
        symbol = request.data.get("symbol")
        if not symbol:
            return HttpResponse("Symbol is required.", status=400)

        # Fetch historical data for the past 30 days
        historical_data = self.get_historical_data(symbol)

        # Get predicted data from the request
        predicted_data = request.data.get("predicted_data", [])
        
        if not predicted_data:
            return HttpResponse("Predicted data is required.", status=400)

        # Generate prediction graph
        prediction_graph_img = generate_prediction_graph(historical_data, predicted_data)

        # Create PDF with the graph
        pdf_buffer = create_pdf_report(
            "Prediction Report",  # No insights image, only the graph
            graph_image=prediction_graph_img
        )
        pdf_path = os.path.join(PDF_SAVE_PATH, "prediction_report.pdf")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)  # Create directory if it doesn't exist
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf_buffer.getvalue())
        # Create HTTP response with PDF
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="prediction_report.pdf"'
        return response

