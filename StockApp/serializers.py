from rest_framework import serializers

from .models import PredictedStockData, StockHistoryData


class StockHistoryDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistoryData
        fields = "__all__"


class PredictedStockDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictedStockData
        fields = "__all__"


class BacktestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    initial_investment = serializers.DecimalField(max_digits=10, decimal_places=2)
    short_moving_average = serializers.IntegerField()
    long_moving_average = serializers.IntegerField()
