# urls.py
from django.urls import path
from .views import get_stock_history_data,get_stock_data_by_symbol_api,get_all_stock_data,generate_report_view,BacktestView,predict_stock_prices_api,get_predicted_data,GenerateBacktestReportView,GeneratePredictionReportView

urlpatterns = [
    path('stock/', get_stock_history_data, name='get_stock_history_data'),
    path('stocks/', get_all_stock_data, name='get_all_stock_data'),
    path('stock/<str:symbol>/', get_stock_data_by_symbol_api, name='get_stock_data_by_symbol_api'),
    path('backtest/', BacktestView.as_view(), name='run_backtest_view'),
    path('generate_report/', generate_report_view, name='generate_report_view'),
    path('predict/<str:symbol>/', predict_stock_prices_api, name='predict_stock_prices_api'),
    path('predicted-data/<str:symbol>/', get_predicted_data, name='get_predicted_data'),
    path('reports/backtest/', GenerateBacktestReportView.as_view(), name='generate_backtest_report'),
    path('reports/prediction/', GeneratePredictionReportView.as_view(), name='generate_prediction_report'),
]
