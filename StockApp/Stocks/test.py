import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone
from StockApp.Stocks.tasks import fetch_stock_data_from_alpha_api, save_stock_data
from StockApp.models import StockHistoryData
import requests
class BaseTestCase:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.symbol = 'AAPL'
        self.time_series = {
            "2023-04-14": {
                "1. open": "100.0",
                "2. high": "101.0",
                "3. low": "99.0",
                "4. close": "100.5",
                "5. volume": "1000000"
            }
        }
        self.two_years_ago = timezone.now() - timedelta(days=2 * 365)
        self.two_years_ago_timestamp = int(self.two_years_ago.timestamp())

    @pytest.fixture
    def mock_response(self):
        mock = MagicMock()
        mock.json.return_value = {
            "Time Series (Daily)": self.time_series
        }
        return mock

    @pytest.fixture
    def mock_save_stock_data(self):
        with patch('StockApp.Stocks.tasks.save_stock_data') as mock:
            yield mock

class TestFetchStockData(BaseTestCase):
    def test_fetch_stock_data_success(self, mock_response, mock_save_stock_data):
        with patch('requests.get', return_value=mock_response):
            result = fetch_stock_data_from_alpha_api(self.symbol)
        
        assert result == f"Data for {self.symbol} stored successfully."
        mock_save_stock_data.assert_called_once()

    def test_fetch_stock_data_api_limit_reached(self, mock_response):
        mock_response.json.return_value = {"Information": "API limit reached"}
        with patch('requests.get', return_value=mock_response):
            result = fetch_stock_data_from_alpha_api(self.symbol)
        
        assert result == {"error": "Alpha Vantage API Rate Limit Reached"}

    def test_fetch_stock_data_invalid_response(self, mock_response):
        mock_response.json.return_value = {"Note": "Invalid API call"}
        with patch('requests.get', return_value=mock_response):
            result = fetch_stock_data_from_alpha_api(self.symbol)
        
        assert result == f"Error fetching data for {self.symbol}: Invalid API call"

    def test_fetch_stock_data_request_exception(self):
        with patch('requests.get', side_effect=requests.RequestException("Connection error")):
            result = fetch_stock_data_from_alpha_api(self.symbol)
        
        assert result == "Error fetching data from Alpha API: Connection error"

class TestSaveStockData(BaseTestCase):
    def test_save_stock_data(self):
        result = save_stock_data(self.symbol, self.time_series, self.two_years_ago_timestamp)

        assert result is None
        saved_data = StockHistoryData.objects.filter(symbol=self.symbol).first()
        assert saved_data is not None
        assert saved_data.open_price == 100.0
        assert saved_data.close_price == 100.5
        assert saved_data.volume == 1000000

    def test_save_stock_data_integrity_error(self):

        StockHistoryData.objects.create(
            symbol=self.symbol,
            timestamp=int(datetime.strptime("2023-04-14", "%Y-%m-%d").timestamp()),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000000
        )

        result = save_stock_data(self.symbol, self.time_series, self.two_years_ago_timestamp)

        assert result == f"Error saving data for {self.symbol}: UNIQUE constraint failed."

