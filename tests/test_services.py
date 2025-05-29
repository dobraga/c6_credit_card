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


def test_plot_next_months_basic():
    """Test plot_next_months with basic data."""
    # Sample DataFrame for a MockFile
    df_data = pd.DataFrame({
        'type': ['compra', 'recorrente', 'parcela', 'parcela'],
        'valor': [50, 30, 100, 100],
        'parcela': [0, 0, 1, 2], # parcela 1 de 2, parcela 2 de 2
        'parcelas_faltantes': [0, 0, 1, 0] # 1 parcela restante for first, 0 for second
    })
    mock_file = MockFile(df_data=df_data)
    
    # Expected: recorrentes = 30
    # Parcelas:
    # Parcela 1 (valor 100, faltantes 1): this is the one that counts for future.
    # max_index = 1
    # arr = [nan, 100.0]
    # parcelas series = [100.0] (index 0, representing 1 month from now)
    # parcelas_rec = [130.0]
    
    ys, xs = plot_next_months(mock_file)
    
    # Based on the logic in services.py:
    # recorrentes = 30
    # parcelas = series with value 100 at index 0 (representing 1 month from now)
    # parcelas_rec = 100 + 30 = 130
    # ys = [130.0], xs = [0] (if index is 0-based for months from now)
    # The `plot_next_months` function in services.py has:
    # parcelas = pd.Series(arr[1:], name="parcelas_faltantes").ffill().fillna(0)
    # xs = parcelas_rec.index.tolist()
    # If max_index is 1, arr[1:] is [100.0]. Index will be [0].
    
    assert ys == [130.0]
    assert xs == [0] # Index of the series, representing months from now

def test_plot_next_months_no_future_parcels():
    df_data = pd.DataFrame({
        'type': ['compra', 'recorrente'],
        'valor': [50, 30],
        'parcela': [0, 0],
        'parcelas_faltantes': [0, 0]
    })
    mock_file = MockFile(df_data=df_data)
    ys, xs = plot_next_months(mock_file)

    # recorrentes = 30. No parcelas_faltantes > 0.
    # max_index will be 0 (due to `if parcelas.keys() else 0`)
    # arr = [nan]
    # parcelas = pd.Series(arr[1:]...) will be an empty series
    # parcelas.fillna(0) will still be empty
    # parcelas_rec = empty_series + 30 = series of [30.0] if using broadcasting rules for empty series, or might error.
    # The code has `parcelas = pd.Series(arr[1:], name="parcelas_faltantes").ffill().fillna(0)`
    # If arr[1:] is empty, pd.Series([]) + 30 is tricky.
    # If max_index = 0, arr = [np.nan]. arr[1:] is empty. pd.Series([], name="parcelas_faltantes", dtype=float64)
    # parcelas_rec = pd.Series([], dtype=float64) + 30 = pd.Series([], dtype=float64)
    # So ys and xs should be empty.
    assert ys == [] # This depends on how pandas handles Series + scalar with empty series.
                     # If parcelas_rec remains empty, then .values.tolist() is []
    assert xs == []

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

    assert tps == ['food', 'other', 'transport'] # Order might vary based on groupby and sort
    
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
