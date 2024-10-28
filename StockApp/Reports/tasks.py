import base64
import io
import os
import tempfile
from datetime import datetime
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from celery import shared_task
import json
from django.http import HttpResponse

# Constants
FONT_HELVETICA = "Helvetica"
FONT_HELVETICA_BOLD = "Helvetica-Bold"
TITLE_FONT_SIZE = 16
BODY_FONT_SIZE = 12
MARGIN_LEFT = 100
MARGIN_TOP = 50
GRAPH_WIDTH = 400
GRAPH_HEIGHT = 200
MIN_Y_POSITION = 100

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def convert_to_timestamp(item):
    try:
        if isinstance(item["timestamp"], str):
            return int(datetime.strptime(item["timestamp"], "%Y-%m-%d").timestamp())
        return int(item["timestamp"])
    except (KeyError, ValueError) as e:
        logger.error(f"Error converting timestamp: {e}")
        raise ValueError(f"Invalid timestamp format in item: {item}")


def prepare_plot_data(data):
    try:
        dates = [datetime.fromtimestamp(convert_to_timestamp(item)).strftime("%Y-%m-%d") for item in data]
        prices = [item["price"] for item in data]
        return dates, prices
    except (KeyError, ValueError) as e:
        logger.error(f"Error preparing plot data: {e}")
        raise ValueError(f"Invalid data format: {e}")


def create_plot(ax, historical_data, predicted_data):
    try:
        historical_dates, historical_prices = prepare_plot_data(historical_data)
        predicted_dates, predicted_prices = prepare_plot_data(predicted_data)

        ax.plot(historical_dates, historical_prices, label="Historical Data", color="blue")
        ax.plot(predicted_dates, predicted_prices, label="Predicted Data", color="red")

        ax.set_title("Stock Price Prediction")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True)
        plt.xticks(rotation=45)
    except Exception as e:
        logger.error(f"Error creating plot: {e}")
        raise


def save_plot_to_buffer(fig):
    try:
        img_data = io.BytesIO()
        plt.tight_layout()
        fig.savefig(img_data, format="png")
        img_data.seek(0)
        return img_data
    except Exception as e:
        logger.error(f"Error saving plot to buffer: {e}")
        raise


def generate_prediction_graph(historical, predicted):
    try:
        fig, ax = plt.subplots()
        create_plot(ax, historical, predicted)
        return save_plot_to_buffer(fig)
    except Exception as e:
        logger.error(f"Error generating prediction graph: {e}")
        raise


def generate_backtest_insights(data):
    try:
        metrics = {
            "Final Investment Value": data["Final Investment Value"],
            "Total Return (%)": data["Total Return (%)"],
            "Total Trades": data["Total Trades"],
            "Number of Buys": data["Number of Buys"],
            "Number of Sells": data["Number of Sells"],
            "Maximum Drawdown (%)": data["Maximum Drawdown (%)"],
        }

        fig, ax = plt.subplots()
        ax.axis("tight")
        ax.axis("off")
        table_data = [[k, v] for k, v in metrics.items()]
        ax.table(cellText=table_data, colLabels=["Metric", "Value"], loc="center")
        plt.title("Backtesting Report")

        return save_plot_to_buffer(fig)
    except KeyError as e:
        logger.error(f"Missing key in backtest data: {e}")
        raise ValueError(f"Invalid backtest data format: {e}")
    except Exception as e:
        logger.error(f"Error generating backtest insights: {e}")
        raise


def create_canvas(buffer, pagesize):
    return canvas.Canvas(buffer, pagesize=pagesize)


def draw_title(c, title, y_position):
    c.setFont(FONT_HELVETICA_BOLD, TITLE_FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_position, title)


def draw_metrics(c, data, start_y):
    c.setFont(FONT_HELVETICA, BODY_FONT_SIZE)
    y_position = start_y
    for key, value in data.items():
        if key != "Messages":
            c.drawString(MARGIN_LEFT, y_position, f"{key}: {value}")
            y_position -= 20
    return y_position


def draw_graph(c, graph_image, y_position):
    if graph_image:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(graph_image.getvalue())
                temp_file_path = temp_file.name
            c.drawImage(temp_file_path, MARGIN_LEFT, y_position - GRAPH_HEIGHT, width=GRAPH_WIDTH, height=GRAPH_HEIGHT)
            os.remove(temp_file_path)
            return y_position - (GRAPH_HEIGHT + 20)
        except Exception as e:
            print(f"Error adding image: {e}")
    return y_position


def draw_messages(c, messages, start_y, height):
    try:
        y_position = start_y
        c.drawString(MARGIN_LEFT, y_position, "Trade Messages:")
        y_position -= 20

        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")

        for message in messages:
            if not isinstance(message, str):
                raise ValueError(f"Invalid message type: {type(message)}. Expected string.")

            if y_position < MIN_Y_POSITION:
                c.showPage()
                y_position = height - MARGIN_TOP

            c.drawString(MARGIN_LEFT, y_position, message)
            y_position -= 15

        return y_position
    except Exception as e:
        logger.error(f"Error drawing messages: {e}")
        c.drawString(MARGIN_LEFT, start_y - 20, f"Error drawing messages: {str(e)}")
        return start_y - 40


@shared_task
def generate_pdf_report(backtest_data):
    if isinstance(backtest_data, str):
        try:
            backtest_data = json.loads(backtest_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            raise ValueError("Invalid JSON input")

    # Ensure backtest_data is a dict
    if not isinstance(backtest_data, dict):
        raise TypeError("backtest_data must be a dict or a JSON string")
    graph_image = generate_backtest_insights(backtest_data)
    try:
        buffer = io.BytesIO()
        c = create_canvas(buffer, A4)
        width, height = A4

        draw_title(c, "Backtest Report", height - MARGIN_TOP)
        y_position = draw_metrics(c, backtest_data, height - 80)
        y_position = draw_graph(c, graph_image, y_position)

        if "Messages" in backtest_data:
            draw_messages(c, backtest_data["Messages"], y_position, height)

        c.showPage()
        c.save()
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return pdf_base64
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise


def create_pdf_report(title, graph_image):
    try:
        pdf_buffer = io.BytesIO()
        c = create_canvas(pdf_buffer, letter)

        draw_title(c, title, 750)
        draw_graph(c, graph_image, 400)

        c.showPage()
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        logger.error(f"Error creating PDF report: {e}")
        raise


PDF_SAVE_PATH = "reports/"
BACKTEST_REPORT_FILENAME = "backtest_report.pdf"
PREDICTION_REPORT_FILENAME = "prediction_report.pdf"
HISTORICAL_DATA_DAYS = 30


def ensure_directory_exists(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def save_pdf(pdf_data, filename):
    pdf_path = os.path.join(PDF_SAVE_PATH, filename)
    ensure_directory_exists(pdf_path)

    if isinstance(pdf_data, str):
        pdf_bytes = base64.b64decode(pdf_data)
    else:
        pdf_bytes = pdf_data.getvalue()

    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(pdf_bytes)


@shared_task
def generate_and_save_report(backtest_data):
    # Get base64 string from generate_pdf_report
    pdf_base64 = generate_pdf_report(backtest_data)

    # Convert base64 string back to bytes
    pdf_bytes = base64.b64decode(pdf_base64)

    # Create a BytesIO buffer
    pdf_buffer = io.BytesIO(pdf_bytes)

    # Save the PDF
    save_pdf(pdf_buffer, BACKTEST_REPORT_FILENAME)

    # Return the base64 string
    return pdf_base64


def create_pdf_response(pdf_buffer, filename):
    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
