import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Mocking the File and Files classes as they are complex and involve file system operations
# In a real scenario, these might be more detailed or you might have test-specific versions
class MockFile:
    def __init__(self, path_name="dummy.pdf", df_data=None):
        self.path = MagicMock()
        self.path.name = path_name
        self._df = df_data if df_data is not None else pd.DataFrame()
        # Mock methods that are called by the service functions
        self.summary = MagicMock(return_value=MockSummaryObject())
        self.select = MagicMock(return_value=self) # for chaining or returning a selection

class MockSummaryObject:
    def __init__(self, data=None):
        self.data = data if data is not None else pd.DataFrame()
        # Mock methods of Summary object if any are used by services
        self.print = MagicMock(return_value="Mocked Print Output")
        self.top = MagicMock(return_value=self)
        self.sort = MagicMock(return_value=self)


class MockFiles:
    def __init__(self, files_list=None):
        self._files = files_list if files_list is not None else []
        self.summary_all = MagicMock(return_value=pd.DataFrame()) # Default empty DF

    def __getitem__(self, index):
        return self._files[index]

    def process(self, pswd, force):
        # Mock processing
        pass


# Now, import the functions to be tested from your services module
from c6_credit_card.services import (
    plot_data_total,
    plot_next_months,
    plot_data_type,
    # read_files, # This will require more complex mocking
    # plot_gastos_por_dia
)

def test_plot_data_total_empty():
    """Test plot_data_total with no files or empty summary."""
    mock_files = MockFiles()
    mock_files.summary_all = MagicMock(return_value=pd.DataFrame(columns=['month', 'tot_value']))
    
    ys, xs = plot_data_total(mock_files)
    
    assert ys == []
    assert xs == []

def test_plot_data_total_with_data():
    """Test plot_data_total with sample data."""
    summary_df = pd.DataFrame({
        'month': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01']),
        'tot_value': [100, 200, 150]
    }).set_index('month') # Assuming summary_all might return a DataFrame with a DatetimeIndex or similar
    
    # The function uses reset_index().sort_values("month")
    # Let's ensure the mock returns data that would result from summary_all()
    mock_files = MockFiles()
    # plot_data_total does: files.summary_all().reset_index().sort_values("month")
    # So, the mock should return something that reset_index() can be called on.
    # If summary_all returns a DF with 'month' as a column already, reset_index might not be needed or might change things.
    # Let's assume summary_all() returns a DF where 'month' is in a column, not index.
    mock_data = pd.DataFrame({
        'month': ['2023-01', '2023-02', '2023-03'], # As strings, like typical output from some processing
        'tot_value': [100, 200, 150]
    })
    mock_files.summary_all = MagicMock(return_value=mock_data)
        
    ys, xs = plot_data_total(mock_files)
    
    assert ys == [100, 200, 150]
    assert xs == ['2023-01', '2023-02', '2023-03']


def test_plot_next_months_with_past_and_future():
    """Test plot_next_months with both past and future data."""
    # --- Mocking Setup ---
    # 1. Mock `files` object with historical data
    mock_files = MockFiles()
    summary_df = pd.DataFrame({
        'month': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01']),
        'tot_value': [100, 200, 150]
    })
    mock_files.summary_all = MagicMock(return_value=summary_df)

    # 2. Mock `file` object (latest bill) for future projections
    latest_bill_df = pd.DataFrame({
        'type': ['compra', 'recorrente', 'parcela'],
        'valor': [50, 30, 120],  # 30 for recorrente
        'parcela': [0, 0, 1],
        'parcelas_faltantes': [0, 0, 1]  # 1 remaining installment of 120
    })
    mock_file = MockFile(df_data=latest_bill_df)

    # --- Call the function ---
    ys, xs = plot_next_months(mock_files, mock_file, past_months=3, future_months=2)

    # --- Assertions ---
    # Past: [100, 200, 150]
    # Future: [120 (parcela) + 30 (recorrente), 0 (parcela) + 30 (recorrente)] = [150, 30]
    expected_ys = [100, 200, 150, 150.0, 30.0]
    expected_xs = pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'])

    assert ys == expected_ys
    assert xs == expected_xs.tolist()


def test_plot_next_months_no_future_parcels_with_past():
    """Test plot_next_months with past data but no future installments."""
    # --- Mocking Setup ---
    mock_files = MockFiles()
    summary_df = pd.DataFrame({
        'month': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01']),
        'tot_value': [100, 200, 150]
    })
    mock_files.summary_all = MagicMock(return_value=summary_df)

    latest_bill_df = pd.DataFrame({
        'type': ['compra', 'recorrente'],
        'valor': [50, 30],
        'parcela': [0, 0],
        'parcelas_faltantes': [0, 0]
    })
    mock_file = MockFile(df_data=latest_bill_df)

    # --- Call the function ---
    ys, xs = plot_next_months(mock_files, mock_file, past_months=2, future_months=2)

    # --- Assertions ---
    # Past (2 months): [200, 150]
    # Future: [30 (recorrente), 30 (recorrente)]
    expected_ys = [200, 150, 30.0, 30.0]
    expected_xs = pd.to_datetime(['2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'])

    assert ys == expected_ys
    assert xs == expected_xs.tolist()

def test_plot_data_type_basic():
    mock_files = MockFiles()
    # This function calls files.summary_all("type").reset_index()
    # Then groups by 'type' and 'month'
    summary_data = pd.DataFrame({
        'month': ['2023-01', '2023-01', '2023-02', '2023-02', '2023-01'],
        'type': ['food', 'transport', 'food', 'transport', 'other'],
        'tot_value': [10, 20, 15, 25, 5]
    })
    mock_files.summary_all = MagicMock(return_value=summary_data)

    # Logic will select top 6 types by total value.
    # food: 10+15=25
    # transport: 20+25=45
    # other: 5
    # Expected selected_types: ['transport', 'food', 'other'] (order by sum)
    
    ys, xs, tps = plot_data_type(mock_files)

    assert set(tps) == {'food', 'other', 'transport'}
    
    # Check if transport is one of the types
    assert 'transport' in tps
    idx_transport = tps.index('transport')
    assert xs[idx_transport].tolist() == ['2023-01', '2023-02'] # Assuming original month column is not sorted
    assert ys[idx_transport] == [20, 25]

    assert 'food' in tps
    idx_food = tps.index('food')
    assert xs[idx_food].tolist() == ['2023-01', '2023-02']
    assert ys[idx_food] == [10, 15]

    assert 'other' in tps
    idx_other = tps.index('other')
    assert xs[idx_other].tolist() == ['2023-01']
    assert ys[idx_other] == [5]

# More tests would be needed for read_files (complex mocking) and plot_gastos_por_dia
# For now, these cover the data transformation functions with simpler inputs.
