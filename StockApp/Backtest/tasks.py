import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from celery import shared_task

# Constants
BUY_SIGNAL = True
SELL_SIGNAL = False

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
            moving_averages.append(None)
        else:
            window = prices[i - window_size + 1: i + 1]
            moving_average = sum(window) / window_size
            moving_averages.append(moving_average)
    
    return moving_averages

# def log_debug_info(day, current_price, short_ma_value, long_ma_value):
    # print(f"Day {day}: Price={current_price}, Short MA={short_ma_value}, Long MA={long_ma_value}")

def execute_trade(prices, short_ma, long_ma, initial_investment):
    buy_signal = SELL_SIGNAL
    investment = initial_investment
    shares_held = 0
    num_buys = 0
    num_sells = 0
    messages = []
    peak_investment = initial_investment
    max_drawdown = 0

    for i, current_price in enumerate(prices):
        short_ma_value = short_ma[i] if i >= len(short_ma) else None
        long_ma_value = long_ma[i] if i >= len(long_ma) else None

        # log_debug_info(i + 1, current_price, short_ma_value, long_ma_value)

        if long_ma_value is not None and current_price < long_ma_value and not buy_signal:
            shares_held, investment, buy_signal = buy_shares(investment, current_price)
            num_buys += 1
            messages.append(f"Buy at {current_price} - Total Shares Held: {shares_held}")

        elif short_ma_value is not None and current_price > short_ma_value and buy_signal:
            investment, shares_held, buy_signal = sell_shares(shares_held, current_price)
            num_sells += 1
            messages.append(f"Sell at {current_price} - Investment Value: {investment}")

        peak_investment, max_drawdown = update_drawdown(investment, shares_held, current_price, peak_investment, max_drawdown)

    if shares_held > 0:
        investment = finalize_investment(shares_held, prices[-1])

    return investment, num_buys, num_sells, max_drawdown, messages

def buy_shares(investment, current_price):
    shares_held = float(investment) / float(current_price)
    return shares_held, 0, BUY_SIGNAL

def sell_shares(shares_held, current_price):
    investment = float(shares_held) * float(current_price)
    return investment, 0, SELL_SIGNAL

def update_drawdown(investment, shares_held, current_price, peak_investment, max_drawdown):
    current_value = float(investment) + (float(shares_held) * float(current_price))
    if current_value > peak_investment:
        peak_investment = current_value
    
    drawdown = (float(peak_investment) - float(current_value)) / float(peak_investment)
    max_drawdown = max(max_drawdown, drawdown)
    return peak_investment, max_drawdown

def finalize_investment(shares_held, final_price):
    investment = shares_held * final_price
    print(f"Final Sale at {final_price} - New Investment Value: {investment}")
    return investment


def backtest_strategy(prices, moving_average_short, moving_average_long, initial_investment,symbol):
    if not prices:
        return {"error": f"Price list for {symbol} is empty. Cannot perform backtest."}
    short_ma = [None] * (moving_average_short - 1) + calculate_moving_average(prices, moving_average_short)
    long_ma = [None] * (moving_average_long - 1) + calculate_moving_average(prices, moving_average_long)
    
    investment, num_buys, num_sells, max_drawdown, messages = execute_trade(
        prices, short_ma, long_ma, initial_investment
    )

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