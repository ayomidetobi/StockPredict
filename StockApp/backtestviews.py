# from celery import Celery
# from celery.exceptions import CeleryError, TimeoutError
# from django.views.decorators.cache import cache_page
# from rest_framework import status
# from rest_framework.decorators import api_view, throttle_classes
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle
# from .models import StockHistoryData
# from .backtesttasks import BackTestingUseCase
# # run_backtest_task, generate_backtest_report_task
# from .serializers import StockHistoryDataSerializer
# from .tasks import fetch_stock_data_from_alpha_api
# from django.http import FileResponse
# # from rest_framework import status
# # from rest_framework.decorators import api_view,throttle_classes
# # from rest_framework.response import Response
# # from .tasks import fetch_stock_data_from_alpha_api,run_backtest_task, generate_backtest_report_task
# # from .serializers import StockHistoryDataSerializer
# # from .models import StockHistoryData
# # from django.views.decorators.cache import cache_page
# # from rest_framework.throttling import AnonRateThrottle
# # @api_view(['POST'])
# # def backtest_view(request):
# #     symbol = request.data.get('symbol')
# #     initial_investment = request.data.get('initial_investment')
# #     short_ma_days = request.data.get('short_ma_days')
# #     long_ma_days = request.data.get('long_ma_days')

# #     if not all([symbol, initial_investment, short_ma_days, long_ma_days]):
# #         return {"error": "All parameters are required."}

# #     # Check types of parameters
# #     if not isinstance(symbol, str):
# #         return {"error": "Symbol must be a string."}
# #     if not isinstance(initial_investment, float):
# #         return {"error": "Initial investment must be a float."}
# #     if not isinstance(short_ma_days, int) or short_ma_days <= 0:
# #         return {"error": "Short MA days must be a positive integer."}
# #     if not isinstance(long_ma_days, int) or long_ma_days <= 0:
# #         return {"error": "Long MA days must be a positive integer."}

# #     # Run the backtest task
# #     backtest_result = run_backtest_task.delay(symbol, initial_investment, short_ma_days, long_ma_days)


    
# #     params = {
# #         'symbol': symbol,
# #         'initial_investment': initial_investment,
# #         'short_ma_days': short_ma_days,
# #         'long_ma_days': long_ma_days
# #     }
# #     generate_backtest_report_task.delay(params, backtest_result)

# #     return Response({"task_id": backtest_result.id}, status=status.HTTP_202_ACCEPTED)
# # @api_view(['POST'])
# # def run_backtest(request):
# #     data = request.data
# #     symbol = data.get('symbol')
# #     initial_investment = data.get('initial_investment')
# #     short_ma_days = data.get('short_ma_days')
# #     long_ma_days = data.get('long_ma_days')

# #     if not all([symbol, initial_investment, short_ma_days, long_ma_days]):
# #         return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

# #     results = BackTestingUseCase.run_backtest(symbol, initial_investment, short_ma_days, long_ma_days)
# #     return Response(results)

# # @api_view(['POST'])
# # def generate_report(request):
# #     data = request.data
# #     params = data.get('params')
# #     backtest_results = data.get('backtest_results')

# #     if not params or not backtest_results:
# #         return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

# #     report_file = BackTestingUseCase.generate_backtest_report(params, backtest_results)
# #     return FileResponse(report_file, as_attachment=True, filename='report.pdf')