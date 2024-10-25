import pytest
import io
from datetime import datetime
from unittest.mock import patch, MagicMock
from StockApp.Reports.tasks import (
    convert_to_timestamp,
    prepare_plot_data,
    generate_prediction_graph,
    generate_backtest_insights,
    generate_pdf_report,
    create_pdf_report,
)

@pytest.fixture
def sample_data():
    return [
        {"timestamp": "2023-01-01", "price": 100},
        {"timestamp": "2023-01-02", "price": 101},
        {"timestamp": "2023-01-03", "price": 102},
    ]

def test_convert_to_timestamp():
    assert convert_to_timestamp({"timestamp": "2023-01-01"}) == 1672531200
    assert convert_to_timestamp({"timestamp": 1672531200}) == 1672531200

def test_prepare_plot_data(sample_data):
    dates, prices = prepare_plot_data(sample_data)
    assert dates == ['2023-01-01', '2023-01-02', '2023-01-03']
    assert prices == [100, 101, 102]

@patch('matplotlib.pyplot.subplots')
def test_generate_prediction_graph(mock_subplots, sample_data):
    mock_fig, mock_ax = MagicMock(), MagicMock()
    mock_subplots.return_value = (mock_fig, mock_ax)
    
    result = generate_prediction_graph(sample_data, sample_data)
    
    assert isinstance(result, io.BytesIO)
    mock_ax.plot.assert_called()
    mock_fig.savefig.assert_called()

@patch('matplotlib.pyplot.subplots')
def test_generate_backtest_insights(mock_subplots):
    mock_fig, mock_ax = MagicMock(), MagicMock()
    mock_subplots.return_value = (mock_fig, mock_ax)
    
    data = {
        "Final Investment Value": 1000,
        "Total Return (%)": 10,
        "Total Trades": 5,
        "Number of Buys": 3,
        "Number of Sells": 2,
        "Maximum Drawdown (%)": 5,
    }
    
    result = generate_backtest_insights(data)
    
    assert isinstance(result, io.BytesIO)
    mock_ax.table.assert_called()
    mock_fig.savefig.assert_called()

@patch('StockApp.Reports.tasks.create_canvas')
@patch('StockApp.Reports.tasks.draw_title')
@patch('StockApp.Reports.tasks.draw_metrics')
@patch('StockApp.Reports.tasks.draw_graph')
@patch('StockApp.Reports.tasks.draw_messages')
def test_generate_pdf_report(mock_draw_messages, mock_draw_graph, mock_draw_metrics, mock_draw_title, mock_create_canvas):
    mock_canvas = MagicMock()
    mock_create_canvas.return_value = mock_canvas
    
    backtest_data = {
        "Final Investment Value": 1000,
        "Total Return (%)": 10,
        "Messages": ["Trade 1", "Trade 2"],
    }
    graph_image = io.BytesIO(b"fake image data")
    
    result = generate_pdf_report(backtest_data, graph_image)
    
    assert isinstance(result, io.BytesIO)
    mock_create_canvas.assert_called()
    mock_draw_title.assert_called()
    mock_draw_metrics.assert_called()
    mock_draw_graph.assert_called()
    mock_draw_messages.assert_called()
    mock_canvas.showPage.assert_called()
    mock_canvas.save.assert_called()

@patch('StockApp.Reports.tasks.create_canvas')
@patch('StockApp.Reports.tasks.draw_title')
@patch('StockApp.Reports.tasks.draw_graph')
def test_create_pdf_report(mock_draw_graph, mock_draw_title, mock_create_canvas):
    mock_canvas = MagicMock()
    mock_create_canvas.return_value = mock_canvas
    
    title = "Test Report"
    graph_image = io.BytesIO(b"fake image data")
    
    result = create_pdf_report(title, graph_image)
    
    assert isinstance(result, io.BytesIO)
    mock_create_canvas.assert_called()
    mock_draw_title.assert_called_with(mock_canvas, title, 750)
    mock_draw_graph.assert_called_with(mock_canvas, graph_image, 400)
    mock_canvas.showPage.assert_called()
    mock_canvas.save.assert_called()