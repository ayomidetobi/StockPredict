import os
from datetime import datetime, timedelta
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from .tasks import generate_backtest_insights, generate_prediction_graph, create_pdf_report, generate_pdf_report
from StockApp.models import StockHistoryData
from rest_framework.decorators import throttle_classes
from rest_framework.response import Response
from rest_framework import status

# Constants
PDF_SAVE_PATH = "reports/"
BACKTEST_REPORT_FILENAME = "backtest_report.pdf"
PREDICTION_REPORT_FILENAME = "prediction_report.pdf"
HISTORICAL_DATA_DAYS = 30

class GenerateReportMixin:
    @staticmethod
    def ensure_directory_exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    @staticmethod
    def save_pdf(pdf_buffer, filename):
        pdf_path = os.path.join(PDF_SAVE_PATH, filename)
        GenerateReportMixin.ensure_directory_exists(pdf_path)
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf_buffer.getvalue())

    @staticmethod
    def create_pdf_response(pdf_buffer, filename):
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

@throttle_classes([AnonRateThrottle])
class GenerateBacktestReportView(APIView, GenerateReportMixin):
    def post(self, request, *args, **kwargs):
        data = request.data
        
        backtest_data = self.validate_request_data(data)
        if isinstance(backtest_data, Response):
            return backtest_data
        
        validation_result = self.validate_backtest_data(backtest_data)
        if isinstance(validation_result, Response):
            return validation_result
        
        return self.generate_and_save_report(backtest_data)

    @staticmethod
    def validate_request_data(data):
        if 'results' not in data:
            return Response({"error": "'results' key is missing in the request data."}, status=status.HTTP_400_BAD_REQUEST)
        
        backtest_data = data['results']
        if not isinstance(backtest_data, dict):
            return Response({"error": "'results' must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)
        
        return backtest_data

    @staticmethod
    def validate_backtest_data(backtest_data):
        required_fields = {
            "Final Investment Value": float,
            "Total Return (%)": float,
            "Total Trades": int,
            "Number of Buys": int,
            "Number of Sells": int,
            "Maximum Drawdown (%)": float,
            "Messages": list
        }
        
        missing_fields, incorrect_type_fields = [], []
        
        for field, field_type in required_fields.items():
            if field not in backtest_data:
                missing_fields.append(field)
            elif not isinstance(backtest_data[field], field_type):
                incorrect_type_fields.append(f"{field} (expected {field_type.__name__})")
        
        if missing_fields:
            return Response({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if incorrect_type_fields:
            return Response({"error": f"Incorrect data types for fields: {', '.join(incorrect_type_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return None

    def generate_and_save_report(self, backtest_data):
        insights_img = generate_backtest_insights(backtest_data)
        pdf_buffer = generate_pdf_report(backtest_data, graph_image=insights_img)
        
        self.save_pdf(pdf_buffer, BACKTEST_REPORT_FILENAME)
        return self.create_pdf_response(pdf_buffer, BACKTEST_REPORT_FILENAME)

class GeneratePredictionReportView(APIView, GenerateReportMixin):
    throttle_classes = [AnonRateThrottle]

    @staticmethod
    def get_historical_data(symbol):
        try:
            date_30_days_ago = datetime.now() - timedelta(days=HISTORICAL_DATA_DAYS)
            timestamp_30_days_ago = int(date_30_days_ago.timestamp())

            historical_data = StockHistoryData.objects.filter(
                symbol=symbol.upper(), 
                timestamp__gte=timestamp_30_days_ago
            ).order_by('timestamp')

            return [
                {
                    "timestamp": datetime.fromtimestamp(data.timestamp).strftime('%Y-%m-%d'),
                    "price": data.close_price
                } for data in historical_data
            ]
        except Exception as e:
            print(f"Failed to retrieve historical data for symbol {symbol}: {e}")
            raise

    def post(self, request, *args, **kwargs):
        symbol = request.data.get("symbol")
        if not symbol:
            return Response("Symbol is required.", status=status.HTTP_400_BAD_REQUEST)

        historical_data = self.get_historical_data(symbol)
        predicted_data = request.data.get("predicted_data", [])
        
        if not predicted_data:
            return Response("Predicted data is required.", status=status.HTTP_400_BAD_REQUEST)

        prediction_graph_img = generate_prediction_graph(historical_data, predicted_data)
        pdf_buffer = create_pdf_report("Prediction Report", graph_image=prediction_graph_img)
        
        self.save_pdf(pdf_buffer, PREDICTION_REPORT_FILENAME)
        return self.create_pdf_response(pdf_buffer, PREDICTION_REPORT_FILENAME)