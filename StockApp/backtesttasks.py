import pandas as pd
# from .utils import get_stock_data_by_symbol
import matplotlib.pyplot as plt
from fpdf import FPDF


from celery import shared_task
# @shared_task
def calculate_moving_average(prices, window_size):
    if not isinstance(prices, list):
        raise TypeError("Prices should be a list.")
    
    if not all(isinstance(price, (int, float)) for price in prices):
        raise TypeError("All elements in prices should be integers or floats.")
    
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError("Window size must be a positive integer.")
    
    if len(prices) < window_size:
        return [None] * len(prices)
    
    moving_averages = []
    for i in range(len(prices)):
        if i < window_size - 1:
            moving_averages.append(None)  # Not enough data points to calculate
        else:
            window = prices[i - window_size + 1: i + 1]
            moving_average = sum(window) / window_size
            moving_averages.append(moving_average)
    
    return moving_averages

# Example usage:





def backtest_strategy(prices, moving_average_short, moving_average_long, initial_investment):
    buy_signal = False
    investment = initial_investment
    shares_held = 0
    num_buys = 0
    num_sells = 0
    messages = []

    # Variables for calculating maximum drawdown
    peak_investment = initial_investment
    max_drawdown = 0

    # Pre-calculate the moving averages for the short and long windows
    short_ma = [None] * (moving_average_short - 1) + calculate_moving_average(prices, moving_average_short)
    long_ma = [None] * (moving_average_long - 1) + calculate_moving_average(prices, moving_average_long)

    # Iterate over the price list
    for i in range(len(prices)):
        current_price = prices[i]
        short_ma_value = short_ma[i] if i >= moving_average_short - 1 else None
        long_ma_value = long_ma[i] if i >= moving_average_long - 1 else None

        # Log moving averages and price for debugging
        print(f"Day {i+1}: Price={current_price}, Short MA={short_ma_value}, Long MA={long_ma_value}")

        # Check if we should buy
        if long_ma_value is not None and current_price < long_ma_value and not buy_signal:
            # Buy signal: current price dips below the long moving average
            shares_held = float(investment) / float(current_price)
            investment = 0 
            buy_signal = True
            num_buys += 1
            messages.append(f"Buy at {current_price} - Total Shares Held: {shares_held}")

        # Check if we should sell
        elif short_ma_value is not None and current_price > short_ma_value and buy_signal:
            # Sell signal: current price goes above the short moving average
            investment = float(shares_held) * float(current_price)  # Update investment to reflect current value
            shares_held = 0
            buy_signal = False
            num_sells += 1
            messages.append(f"Sell at {current_price} - Investment Value: {investment}")

        # Track peak value and calculate drawdown
        current_value = float(investment) + (float(shares_held) * float(current_price))
        if current_value > peak_investment:
            peak_investment = current_value
        
        drawdown = (float(peak_investment) - float(current_value)) / float(peak_investment)
        max_drawdown = max(max_drawdown, drawdown)

    # Ensure final sale if shares are still held
    if shares_held > 0:
        investment = shares_held * prices[-1]
        print(f"Final Sale at {prices[-1]} - New Investment Value: {investment}")

    total_trades = num_buys + num_sells
    total_return = (float(investment) - float(initial_investment)) / float(initial_investment)

    return {
        "Final Investment Value": round(investment, 2),
        "Total Return (%)": round(total_return * 100, 2),
        "Total Trades": total_trades,
        "Number of Buys": num_buys,
        "Number of Sells": num_sells,
        "Maximum Drawdown (%)": round(max_drawdown * 100, 2),
        "Messages": messages
    }




# 