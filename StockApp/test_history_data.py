from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import SoftTimeLimitExceeded, TimeoutError
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from StockApp.models import StockHistoryData
from StockApp.tasks import fetch_stock_data_from_alpha_api


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def valid_symbol():
    return "AAPL"


@pytest.fixture
def invalid_symbol():
    return "INVALIDSYM"


@pytest.fixture
def mock_delay():
    with patch("StockApp.views.fetch_stock_data_from_alpha_api.delay") as mock:
        yield mock


@pytest.fixture
def sample_api_data():
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2024-10-22",
            "4. Output Size": "Full size",
            "5. Time Zone": "US/Eastern",
        },
        "Time Series (Daily)": {
            "2024-10-22": {
                "1. open": "21.9800",
                "2. high": "22.0500",
                "3. low": "21.9600",
                "4. close": "21.9800",
                "5. volume": "8133019",
            },
            "2024-10-21": {
                "1. open": "21.9800",
                "2. high": "22.0500",
                "3. low": "21.9600",
                "4. close": "21.9800",
                "5. volume": "8133019",
            },
        },
    }


@pytest.mark.django_db
class TestFetchStockData:
    @patch("requests.get")
    def test_fetch_stock_data_within_past_two_years(self, mock_get, sample_api_data):
        mock_get.return_value.json.return_value = sample_api_data
        fetch_stock_data_from_alpha_api("AAPL")

        two_years_ago = timezone.now() - timedelta(days=2 * 365)
        two_years_ago_timestamp = int(two_years_ago.timestamp())

        recent_data = StockHistoryData.objects.filter(
            symbol="AAPL", timestamp__gte=two_years_ago_timestamp
        )
        assert recent_data.count() == 1


@pytest.mark.django_db
class TestGetStockHistoryData:
    @pytest.fixture(autouse=True)
    def setup_class(self, api_client, valid_symbol, invalid_symbol):
        self.client = api_client
        self.valid_symbol = valid_symbol
        self.invalid_symbol = invalid_symbol
        self.url = reverse("get_stock_history_data")

    def test_missing_symbol(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Symbol is required and must be a string."}

    def test_invalid_symbol_type(self):
        response = self.client.post(self.url, {"symbol": 1234})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Symbol is required and must be a string."}

    def test_unique_constraint_error(self, mock_delay):
        mock_delay.return_value.get.side_effect = IntegrityError("UNIQUE constraint failed")

        response = self.client.post(self.url, {"symbol": self.valid_symbol})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "UNIQUE constraint failed" in response.data["error"]

    def test_timeout_error(self, mock_delay):
        mock_delay.return_value.get.side_effect = TimeoutError()

        response = self.client.post(self.url, {"symbol": self.valid_symbol})
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert (
            f"Data fetching for {self.valid_symbol} is now being processed in the background."
            in response.data["message"]
        )

    def test_invalid_symbol(self, mock_delay):
        mock_delay.return_value.get.return_value = (
            f"Error fetching data for {self.invalid_symbol}: Invalid API response"
        )

        response = self.client.post(self.url, {"symbol": self.invalid_symbol})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error fetching data for" in response.data["error"]

    @patch("StockApp.tasks.save_stock_data")
    def test_unexpected_error_in_save(self, mock_save_stock_data, mock_delay):
        mock_save_stock_data.side_effect = Exception("Unexpected error during saving data")

        mock_delay.return_value.get.return_value = (
            "An unexpected error occurred: Unexpected error during saving data"
        )

        response = self.client.post(self.url, {"symbol": self.valid_symbol})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "An unexpected error occurred:" in response.data["error"]

    def test_successful_data_fetch(self, mock_delay):
        mock_delay.return_value.get.return_value = (
            f"Data for {self.valid_symbol} stored successfully."
        )

        response = self.client.post(self.url, {"symbol": self.valid_symbol})
        assert response.status_code == status.HTTP_200_OK
        assert f"Data for {self.valid_symbol} stored successfully." in response.data["message"]
