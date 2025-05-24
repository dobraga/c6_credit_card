import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

# Mocking File and Files as in test_services
class MockFile:
    def __init__(self, path_name="dummy.pdf", df_data=None):
        self.path = MagicMock()
        self.path.name = path_name
        self._df = df_data if df_data is not None else pd.DataFrame()
        self.summary = MagicMock(return_value=MockSummaryObject())
        self.select = MagicMock(return_value=self)
        self.top = MagicMock(return_value=self) # Ensure top returns self for chaining
        self.print = MagicMock(return_value="Mocked Print Output From MockFile") # Add mock print method

    @property
    def data(self):
        # This makes .data behave like a property, returning the internal DataFrame
        return self._df

class MockSummaryObject:
    def __init__(self, data=None):
        # Ensure data is a DataFrame, even if empty, with expected columns if possible
        if data is None:
            self.data = pd.DataFrame(columns=['type', 'tot_value', 'local', 'qtd', 'parcelas_faltantes'])
        else:
            self.data = data
        self.print = MagicMock(return_value="Mocked Print Output")
        self.top = MagicMock(return_value=self)
        self.sort = MagicMock(return_value=self)

class MockFiles:
    def __init__(self, files_list=None):
        self._files = files_list if files_list is not None else []

    def __getitem__(self, index):
        return self._files[index]


from c6_credit_card.output import display_terminal_output, generate_html_output

@pytest.fixture
def mock_console():
    return MagicMock()

@pytest.fixture
def sample_file_data():
    # Provides a common set of data for testing output functions
    file_df = pd.DataFrame({
        'type': ['compra', 'recorrente', 'parcela'],
        'valor': [50, 30, 100],
        'parcela': [0,0,1],
        'parcelas_faltantes': [0,0,1],
        'local': ['Supermercado', 'Netflix', 'Loja XYZ']
    })
    file = MockFile(df_data=file_df)
    
    # Mocking the data returned by file.summary("type").data etc.
    # This needs to align with what generate_html_output expects from summary_obj.data
    # Updated side_effect for file.summary to handle kwargs
    def summary_side_effect(summary_type, **kwargs): # Corrected indentation
        if summary_type == "type":
            return MockSummaryObject(data=pd.DataFrame({
                'type': ['compra', 'recorrente', 'parcela', 'total'], 
                'tot_value': [50, 30, 100, 180]
            }))
        elif summary_type == "local":
            return MockSummaryObject(data=pd.DataFrame({
                'local': ['Supermercado', 'Netflix', 'Loja XYZ', 'Outro Local'], 
                'tot_value': [50,30,100, 20], 
                'qtd':[1,1,1,1]
            }))
        elif summary_type == "parcelas_faltantes":
                return MockSummaryObject(data=pd.DataFrame({
                'parcelas_faltantes': [0,1], 
                'tot_value': [80,100]
            }))
        return MockSummaryObject() # default empty for other types

    file.summary = MagicMock(side_effect=summary_side_effect) # Correct indentation

    # Mocking file.select().data for tot_avista, tot_parcelados, tot_fin
    select_data_mock = pd.DataFrame({'valor': [10, 20]}) # Generic, adjust if needed
    mock_selected_file = MockFile(df_data=select_data_mock)
    mock_selected_file.top = MagicMock(return_value=mock_selected_file) # for .top(10)
    file.select = MagicMock(return_value=mock_selected_file)


    files = MockFiles(files_list=[file])
    
    return {
        "file": file,
        "files": files,
        "ys_next_months": [130.0], "xs_next_months": [0], # from test_services example
        "ys_data_total": [100, 200], "xs_data_total": ['2023-01', '2023-02'],
        "ys_data_type": [[10, 15], [20, 25]], 
        "xs_data_type": [['2023-01', '2023-02'], ['2023-01', '2023-02']],
        "tps_data_type": ['food', 'transport']
    }

def test_display_terminal_output_runs(mock_console, sample_file_data):
    """Test that display_terminal_output runs without errors with mock data."""
    try:
        display_terminal_output(
            CONSOLE=mock_console,
            file=sample_file_data["file"],
            files=sample_file_data["files"],
            ys_next_months=sample_file_data["ys_next_months"],
            xs_next_months=sample_file_data["xs_next_months"],
            ys_data_total=sample_file_data["ys_data_total"],
            xs_data_total=sample_file_data["xs_data_total"],
            ys_data_type=sample_file_data["ys_data_type"],
            xs_data_type=sample_file_data["xs_data_type"],
            tps_data_type=sample_file_data["tps_data_type"],
        )
    except Exception as e:
        pytest.fail(f"display_terminal_output raised an exception: {e}")
    
    # Check if console.print was called (basic check)
    mock_console.print.assert_called()

def test_generate_html_output_basic_structure(sample_file_data):
    """Test that generate_html_output produces a string with basic HTML tags."""
    html_content = generate_html_output(
        file=sample_file_data["file"],
        files=sample_file_data["files"],
        ys_next_months=sample_file_data["ys_next_months"],
        xs_next_months=sample_file_data["xs_next_months"],
        ys_data_total=sample_file_data["ys_data_total"],
        xs_data_total=sample_file_data["xs_data_total"],
        ys_data_type=sample_file_data["ys_data_type"],
        xs_data_type=sample_file_data["xs_data_type"],
        tps_data_type=sample_file_data["tps_data_type"],
    )
    
    assert isinstance(html_content, str)
    assert "<h1>C6 Credit Card Analysis</h1>" in html_content
    assert "<table" in html_content # Check for table presence (more flexible)
    assert f"Report for file: {sample_file_data['file'].path.name}" in html_content

def test_generate_html_output_data_presence(sample_file_data):
    """Test that generate_html_output includes some key data in the HTML."""
    # Modify sample_file_data for more specific checks if needed
    sample_file_data["file"].path.name = "test_bill.pdf"
    sample_file_data["ys_data_total"] = [500, 600]
    sample_file_data["xs_data_total"] = ['2024-01', '2024-02']
    
    html_content = generate_html_output(
        file=sample_file_data["file"],
        files=sample_file_data["files"],
        ys_next_months=sample_file_data["ys_next_months"],
        xs_next_months=sample_file_data["xs_next_months"],
        ys_data_total=sample_file_data["ys_data_total"],
        xs_data_total=sample_file_data["xs_data_total"],
        ys_data_type=sample_file_data["ys_data_type"],
        xs_data_type=sample_file_data["xs_data_type"],
        tps_data_type=sample_file_data["tps_data_type"],
    )
    
    assert "test_bill.pdf" in html_content
    assert "<td>500</td>" in html_content or ">500</td>" in html_content # Value from ys_data_total
    assert "<td>2024-01</td>" in html_content or ">2024-01</td>" in html_content # Value from xs_data_total
    assert "food" in html_content # from tps_data_type
    
    # Check for summary data (e.g. from file.summary("type").data)
    # Based on the mock setup for sample_file_data:
    # file.summary("type") returns a MockSummaryObject with data
    # {'type': ['compra', 'recorrente', 'parcela', 'total'], 'tot_value': [50, 30, 100, 180]}
    assert "<td>compra</td>" in html_content
    assert "<td>180</td>" in html_content # Total value
    assert "<td>Supermercado</td>" in html_content # from local summary data

    # Check for a value from the mocked file.select().data
    # tot_avista etc. use file.select().top(10).data
    # The MockFile.select returns a MockFile whose data is select_data_mock = pd.DataFrame({'valor': [10, 20]})
    assert "<td>10</td>" in html_content # from the select_data_mock
    assert "<td>20</td>" in html_content # from the select_data_mock
