from django.db import models
import datetime



class BaseStockData(models.Model):
    symbol = models.CharField(max_length=10)
    timestamp = models.BigIntegerField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if isinstance(self.timestamp, datetime.datetime):
            self.timestamp = int(self.timestamp.timestamp())
        super().save(*args, **kwargs)

class StockHistoryData(BaseStockData):
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)
    class Meta:
        unique_together = ('symbol', 'timestamp')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['symbol', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.timestamp}"

class PredictedStockData(BaseStockData):
    predicted_close_price = models.DecimalField(max_digits=20, decimal_places=8)
    predicted_open_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    predicted_high_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    predicted_low_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    predicted_volume = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('symbol', 'timestamp')
        ordering = ['-timestamp']
    def __str__(self):
        return f"{self.symbol} - Predicted on {self.timestamp}"