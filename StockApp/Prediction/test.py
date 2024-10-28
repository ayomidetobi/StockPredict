import pytest
from datetime import datetime, timedelta
import pandas as pd
from django.utils import timezone
from unittest.mock import patch, MagicMock

from StockApp.Prediction.tasks import (
    prepare_data_for_prophet,
    fit_prophet_model,
    predict_single_feature,
    predict_all_features,
    create_prediction_data,
    store_predictions,
    predict_and_store,
)
from StockApp.models import PredictedStockData


# Mock data
@pytest.fixture
def mock_stock_data():
    return [
        MagicMock(
            timestamp=int((datetime.now() - timedelta(days=i)).timestamp()),
            open_price=100 + i,
            high_price=105 + i,
            low_price=95 + i,
            close_price=102 + i,
            volume=1000000 + i * 1000,
        )
        for i in range(30)
    ]


@pytest.fixture
def mock_predictions():
    return {
        "open_price": [{"ds": datetime.now() + timedelta(days=i), "open_price": 100 + i} for i in range(30)],
        "high_price": [{"ds": datetime.now() + timedelta(days=i), "high_price": 105 + i} for i in range(30)],
        "low_price": [{"ds": datetime.now() + timedelta(days=i), "low_price": 95 + i} for i in range(30)],
        "close_price": [{"ds": datetime.now() + timedelta(days=i), "close_price": 102 + i} for i in range(30)],
        "volume": [{"ds": datetime.now() + timedelta(days=i), "volume": 1000000 + i * 1000} for i in range(30)],
    }


# Tests
@patch("StockApp.Prediction.tasks.get_all_data_by_symbol")
def test_prepare_data_for_prophet(mock_get_all_data, mock_stock_data):
    mock_get_all_data.return_value = mock_stock_data
    result = prepare_data_for_prophet("AAPL")
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["ds", "open_price", "high_price", "low_price", "close_price", "volume"]
    assert len(result) == 30


def test_fit_prophet_model():
    df = pd.DataFrame({"ds": pd.date_range(start="2023-01-01", periods=30), "open_price": range(100, 130)})
    model = fit_prophet_model(df, "open_price")
    assert model.history.shape[0] == 30


@patch("StockApp.Prediction.tasks.Prophet")
def test_predict_single_feature(mock_prophet):
    mock_model = MagicMock()
    mock_model.predict.return_value = pd.DataFrame(
        {"ds": pd.date_range(start="2023-01-01", periods=30), "yhat": range(100, 130)}
    )
    mock_prophet.return_value = mock_model

    future_df = pd.DataFrame({"ds": pd.date_range(start="2023-01-01", periods=30)})
    result = predict_single_feature(mock_model, future_df, "open_price")

    assert len(result) == 30
    assert "ds" in result[0] and "open_price" in result[0]


@patch("StockApp.Prediction.tasks.prepare_data_for_prophet")
@patch("StockApp.Prediction.tasks.fit_prophet_model")
@patch("StockApp.Prediction.tasks.predict_single_feature")
def test_predict_all_features(mock_predict_single, mock_fit_model, mock_prepare_data):
    mock_prepare_data.return_value = pd.DataFrame()
    mock_fit_model.return_value = MagicMock()
    mock_predict_single.return_value = [{"ds": datetime.now(), "feature": 100}]

    result = predict_all_features("AAPL")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"open_price", "high_price", "low_price", "close_price", "volume"}


def test_create_prediction_data(mock_predictions):
    result = create_prediction_data("AAPL", mock_predictions, 0)
    assert result["symbol"] == "AAPL"
    assert "timestamp" in result
    assert "predicted_open_price" in result
    assert "created_at" in result


@patch("StockApp.Prediction.tasks.PredictedStockData.objects.update_or_create")
def test_store_predictions(mock_update_or_create, mock_predictions):
    store_predictions("AAPL", mock_predictions)
    assert mock_update_or_create.call_count == 30


@patch("StockApp.Prediction.tasks.predict_all_features")
@patch("StockApp.Prediction.tasks.store_predictions")
def test_predict_and_store(mock_store, mock_predict):
    mock_predict.return_value = {}
    predict_and_store("AAPL")
    mock_predict.assert_called_once_with("AAPL")
    mock_store.assert_called_once_with("AAPL", {})


# ... You can add more specific tests as needed ...
