from prophet import Prophet
import pandas as pd
from .models import PredictedStockData
from django.utils import timezone
from .utils import get_all_data_by_symbol
from datetime import datetime

def prepare_data_for_prophet(symbol):
    stock_data = get_all_data_by_symbol(symbol)
    if not stock_data:
        raise ValueError(f"No historical data available for symbol: {symbol}")
    
    timestamps = [datetime.fromtimestamp(data.timestamp) for data in stock_data]
    
    # Create DataFrame with all necessary fields
    stock_df = pd.DataFrame({
        'ds': timestamps,  
        'open_price': [float(data.open_price) for data in stock_data],
        'high_price': [float(data.high_price) for data in stock_data],
        'low_price': [float(data.low_price) for data in stock_data],
        'close_price': [float(data.close_price) for data in stock_data],
        'volume': [float(data.volume) for data in stock_data]
    })
    
    return stock_df

def fit_prophet_model(df, target_column):
    df_prophet = df[['ds', target_column]].rename(columns={target_column: 'y'})
    model = Prophet()
    model.fit(df_prophet)
    return model

def predict_all_data(symbol, period=30):
    df = prepare_data_for_prophet(symbol)

    # Initialize models for each required prediction
    models = {
        'open': fit_prophet_model(df, 'open_price'),
        'high': fit_prophet_model(df, 'high_price'),
        'low': fit_prophet_model(df, 'low_price'),
        'close': fit_prophet_model(df, 'close_price'),
        'volume': fit_prophet_model(df, 'volume')
    }

    # Create future dataframe
    future = models['close'].make_future_dataframe(periods=period)

    # Make predictions for each target
    predictions = {}
    for key, model in models.items():
        forecast = model.predict(future)
        predictions[key] = forecast[['ds', 'yhat']].tail(period).rename(columns={'yhat': key}).to_dict(orient='records')

    return predictions

def store_predictions(symbol, predictions):
    for i in range(len(predictions['close'])):
        timestamp = int(predictions['close'][i]['ds'].timestamp())
        predicted_data = {
            'symbol': symbol,
            'timestamp': timestamp,
            'predicted_open_price': float(predictions['open'][i]['open']),
            'predicted_high_price': float(predictions['high'][i]['high']),
            'predicted_low_price': float(predictions['low'][i]['low']),
            'predicted_close_price': float(predictions['close'][i]['close']),
            'predicted_volume': float(predictions['volume'][i]['volume']),
            'created_at': int(timezone.now().timestamp())
        }

        PredictedStockData.objects.update_or_create(
            symbol=symbol,
            timestamp=timestamp,
            defaults=predicted_data
        )
