from .models import StockHistoryData
from datetime import datetime

def get_all_data_by_symbol(symbol):
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string.")
    symbol = symbol.upper()
    try:
        stock_data = StockHistoryData.objects.filter(symbol=symbol)
        return stock_data
    except Exception as e:
        print(f"Failed to retrieve data for {symbol}: {e}")
        raise e


def get_closing_prices_by_symbol(symbol):
    try:
        stock_data = get_all_data_by_symbol(symbol)
        # Extract the 'close' field from each data entry
        closing_prices = [float(data.close_price) for data in stock_data]
        print(closing_prices)
        return closing_prices
    except Exception as e:
        print(f"Failed to get closing prices for {symbol}: {e}")
        raise e


import base64
import io

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def generate_backtest_insights(data):
    """
    Create a PDF page showing key insights from the backtesting results.
    """
    img_data = io.BytesIO()
    fig, ax = plt.subplots()

    metrics = {
        "Final Investment Value": data["Final Investment Value"],
        "Total Return (%)": data["Total Return (%)"],
        "Total Trades": data["Total Trades"],
        "Number of Buys": data["Number of Buys"],
        "Number of Sells": data["Number of Sells"],
        "Maximum Drawdown (%)": data["Maximum Drawdown (%)"],
    }

    ax.axis("tight")
    ax.axis("off")
    table_data = [[k, v] for k, v in metrics.items()]
    table = ax.table(cellText=table_data, colLabels=["Metric", "Value"], loc="center")

    plt.title("Backtesting Report")
    plt.tight_layout()
    plt.savefig(img_data, format="png")
    img_data.seek(0)

    return img_data


def generate_prediction_graph(historical, predicted):
    """
    Plot historical and predicted data on the same graph.
    """
    img_data = io.BytesIO()
    fig, ax = plt.subplots()

    def convert_to_timestamp(item):
        if isinstance(item["timestamp"], str):
            # Assuming the string is in 'YYYY-MM-DD' format
            return int(datetime.strptime(item["timestamp"], '%Y-%m-%d').timestamp())
        return int(item["timestamp"])  # For integer timestamps

    # Convert timestamps to readable dates for the x-axis
    historical_dates = [datetime.fromtimestamp(convert_to_timestamp(item)).strftime('%Y-%m-%d') for item in historical]
    predicted_dates = [datetime.fromtimestamp(convert_to_timestamp(item)).strftime('%Y-%m-%d') for item in predicted]

    historical_prices = [item["price"] for item in historical]
    predicted_prices = [item["price"] for item in predicted]

    # Ensure both x and y data have the same length
    if len(historical_dates) != len(historical_prices):
        raise ValueError("Historical data dates and prices must have the same length.")
    if len(predicted_dates) != len(predicted_prices):
        raise ValueError("Predicted data dates and prices must have the same length.")

    # Plot historical and predicted data
    ax.plot(historical_dates, historical_prices, label="Historical Data", color="blue")
    ax.plot(predicted_dates, predicted_prices, label="Predicted Data", color="red")

    # Add title and legend
    ax.set_title("Stock Price Prediction")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True)

    # Save to BytesIO
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()
    plt.savefig(img_data, format="png")
    img_data.seek(0)

    return img_data



from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import tempfile

def create_pdf_report(title, graph_image):
    """
    Create a PDF report with the given title and graph image.
    """
    pdf_buffer = io.BytesIO()  # Use BytesIO to save the PDF in memory
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Draw title
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, title)

    # Save the graph image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_image_file:
        temp_image_file.write(graph_image.getvalue())  # Write the image data to the file
        temp_image_file_path = temp_image_file.name  # Store the path for later use

    # Draw the graph image in the PDF
    c.drawImage(temp_image_file_path, 50, 50, width=500, height=300)
    
    # Finish the PDF
    c.showPage()
    c.save()

    # Clean up the temporary image file
    os.remove(temp_image_file_path)  # Remove the temp image file after use

    # Move the buffer position to the beginning
    pdf_buffer.seek(0)
    
    return pdf_buffer



from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_pdf_report(backtest_data, graph_image):
    # Create a buffer to hold the PDF data
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title for the PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Backtest Report")

    # Adding backtest data to the PDF
    c.setFont("Helvetica", 12)
    y_position = height - 80

    # Display key metrics
    for key, value in backtest_data.items():
        if key != "Messages":
            c.drawString(100, y_position, f"{key}: {value}")
            y_position -= 20

    # Optionally include the predictive graph if needed
    if graph_image:
        try:
            # Add image if provided (this will keep the parameter compatibility)
            c.drawImage(graph_image, 100, y_position - 200, width=400, height=200)
            y_position -= 220  # Adjust position after adding the image
        except Exception as e:
            print(f"Error adding image: {e}")

    # Handle trade messages (add to the PDF)
    if "Messages" in backtest_data:
        y_position -= 20
        c.drawString(100, y_position, "Trade Messages:")
        y_position -= 20

        # Add each trade message
        for message in backtest_data["Messages"]:
            if y_position < 100:  # Ensure there's space for new page
                c.showPage()
                y_position = height - 80

            c.drawString(100, y_position, message)
            y_position -= 15

    # Finalize the PDF and return it
    c.showPage()
    c.save()

    # Move the buffer to the beginning
    buffer.seek(0)
    return buffer
