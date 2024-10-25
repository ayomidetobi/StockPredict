from datetime import datetime

import pandas as pd
from django.utils import timezone
from prophet import Prophet
from django.db import transaction
from StockApp.models import PredictedStockData
from StockApp.utils import get_all_data_by_symbol

# Constants
PREDICTION_PERIOD = 30
PRICE_COLUMNS = ['open_price', 'high_price', 'low_price', 'close_price']
VOLUME_COLUMN = 'volume'
ALL_COLUMNS = PRICE_COLUMNS + [VOLUME_COLUMN]
DATE_COLUMN = 'ds'
TARGET_COLUMN = 'y'

def prepare_data_for_prophet(symbol):
    stock_data = get_all_data_by_symbol(symbol)
    print("stock_data", stock_data)
    if not stock_data:
        raise ValueError(f"No historical data available for symbol: {symbol}")
    
    return pd.DataFrame({
        DATE_COLUMN: [datetime.fromtimestamp(data.timestamp) for data in stock_data],
        **{col: [float(getattr(data, col)) for data in stock_data] for col in ALL_COLUMNS}
    })

def fit_prophet_model(df, target_column):
    df_prophet = df[[DATE_COLUMN, target_column]].rename(columns={target_column: TARGET_COLUMN})
    model = Prophet()
    model.fit(df_prophet)
    return model

def predict_single_feature(model, future_df, feature_name):
    forecast = model.predict(future_df)
    return forecast[[DATE_COLUMN, 'yhat']].tail(PREDICTION_PERIOD).rename(columns={'yhat': feature_name}).to_dict(orient='records')

def predict_all_features(symbol):
    df = prepare_data_for_prophet(symbol)
    models = {col: fit_prophet_model(df, col) for col in ALL_COLUMNS}
    future_df = models[PRICE_COLUMNS[3]].make_future_dataframe(periods=PREDICTION_PERIOD)
    
    return {
        feature: predict_single_feature(model, future_df, feature)
        for feature, model in models.items()
    }

def create_prediction_data(symbol, predictions, index):
    return {
        'symbol': symbol,
        'timestamp': int(predictions[PRICE_COLUMNS[0]][index][DATE_COLUMN].timestamp()),
        **{f'predicted_{col}': float(predictions[col][index][col]) for col in ALL_COLUMNS},
        'created_at': int(timezone.now().timestamp())
    }

def store_predictions(symbol, predictions):
    # Fetch all existing predictions for the symbol in one query
    existing_predictions = list(PredictedStockData.objects.filter(symbol=symbol))
    existing_pred_dict = {pred.timestamp: pred for pred in existing_predictions}

    predicted_data_list = []
    new_predictions = []

    for i in range(len(predictions[PRICE_COLUMNS[3]])):
        predicted_data = create_prediction_data(symbol, predictions, i)
        timestamp = predicted_data['timestamp']
        
        if timestamp in existing_pred_dict:
            # Update existing prediction
            existing_pred = existing_pred_dict[timestamp]
            for key, value in predicted_data.items():
                setattr(existing_pred, key, value)
            predicted_data_list.append(existing_pred)
        else:
            # Create new prediction
            new_predictions.append(PredictedStockData(**predicted_data))

    with transaction.atomic():
        # Bulk update existing predictions
        if predicted_data_list:
            PredictedStockData.objects.bulk_update(
                predicted_data_list,
                fields=['predicted_' + col for col in ALL_COLUMNS] + ['created_at']
            )
        
        # Bulk create new predictions
        if new_predictions:
            PredictedStockData.objects.bulk_create(new_predictions)

def predict_and_store(symbol):
    predictions = predict_all_features(symbol)
    store_predictions(symbol, predictions)
    return predictions