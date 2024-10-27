# urls.py
from django.urls import path

from .Backtest.views import BacktestView
from .Prediction.views import get_predicted_data, predict_stock_prices_api
from .Reports.views import GenerateBacktestReportView, GeneratePredictionReportView
from .Stocks.views import StockHistoryDataView, AllStockDataView, StockDataBySymbolView

urlpatterns = [
    path('stock/', StockHistoryDataView.as_view(), name='get_stock_history_data'),
    path('stocks/', AllStockDataView.as_view(), name='get_all_stock_data'),
    path('stock/<str:symbol>/', StockDataBySymbolView.as_view(), name='get_stock_data_by_symbol_api'),
    path('backtest/', BacktestView.as_view(), name='run_backtest_view'),
    # path('generate_report/', generate_report_view, name='generate_report_view'),
    path('predict/<str:symbol>/', predict_stock_prices_api, name='predict_stock_prices_api'),
    path('predicted-data/<str:symbol>/', get_predicted_data, name='get_predicted_data'),
    path('reports/backtest/', GenerateBacktestReportView.as_view(), name='generate_backtest_report'),
    path('reports/prediction/', GeneratePredictionReportView.as_view(), name='generate_prediction_report'),
]
