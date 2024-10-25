import pytest
from StockApp.Backtest.tasks import backtest_strategy

def test_backtest_strategy():
    # Sample data for testing
    prices = [100, 105, 102, 110, 108, 115, 120, 125, 130, 128]
    moving_average_short = 3
    moving_average_long = 5
    initial_investment = 1000

    # Call the backtest_strategy function
    result = backtest_strategy(prices, moving_average_short, moving_average_long, initial_investment)

    # Assertions to verify the expected behavior
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "Final Investment Value" in result, "Result should contain 'Final Investment Value'"
    assert "Total Return (%)" in result, "Result should contain 'Total Return (%)'"
    assert "Total Trades" in result, "Result should contain 'Total Trades'"
    assert "Number of Buys" in result, "Result should contain 'Number of Buys'"
    assert "Number of Sells" in result, "Result should contain 'Number of Sells'"
    assert "Maximum Drawdown (%)" in result, "Result should contain 'Maximum Drawdown (%)'"
    assert "Messages" in result, "Result should contain 'Messages'"

    # Example of checking specific values (these will depend on your logic)
    assert result["Final Investment Value"] > 0, "Final Investment Value should be positive"
    assert result["Total Trades"] >= 0, "Total Trades should be non-negative"

# Run the test
