import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

# Import the main function from your CLI script
from c6_credit_card.__main__ import main as cli_main

# Mocking the services and output functions that the CLI calls
# This avoids running the full data processing and output generation logic

@pytest.fixture
def mock_services():
    """Mocks all functions in services.py"""
    with patch('c6_credit_card.__main__.read_files') as mock_read_files, \
         patch('c6_credit_card.__main__.plot_next_months') as mock_plot_next_months, \
         patch('c6_credit_card.__main__.plot_data_total') as mock_plot_data_total, \
         patch('c6_credit_card.__main__.plot_data_type') as mock_plot_data_type:
        
        # Setup default return values for mocks
        # Mock read_files to return a mock Files object which has a mock File item
        mock_file_item = MagicMock()
        mock_file_item.path.name = "mocked_file.pdf"
        # Add other attributes/methods to mock_file_item if main() accesses them directly
        
        mock_files_obj = MagicMock()
        mock_files_obj.__getitem__.return_value = mock_file_item # To mock files[index]
        mock_read_files.return_value = mock_files_obj
        
        mock_plot_next_months.return_value = ([], []) # (ys, xs)
        mock_plot_data_total.return_value = ([], [])  # (ys, xs)
        mock_plot_data_type.return_value = ([], [], []) # (ys, xs, tps)
        
        yield {
            "read_files": mock_read_files,
            "plot_next_months": mock_plot_next_months,
            "plot_data_total": mock_plot_data_total,
            "plot_data_type": mock_plot_data_type,
        }

@pytest.fixture
def mock_output_functions():
    """Mocks functions in output.py"""
    with patch('c6_credit_card.__main__.display_terminal_output') as mock_display_terminal, \
         patch('c6_credit_card.__main__.generate_html_output') as mock_generate_html:
        
        mock_generate_html.return_value = "<html>Mocked HTML Output</html>"
        
        yield {
            "display_terminal": mock_display_terminal,
            "generate_html": mock_generate_html,
        }

def test_cli_basic_invocation(mock_services, mock_output_functions):
    """Test basic CLI invocation with default (terminal) output."""
    runner = CliRunner()
    # Provide a dummy path for '-p' option as it's required
    result = runner.invoke(cli_main, ['-p', 'dummy_path']) 
    
    assert result.exit_code == 0
    mock_services["read_files"].assert_called_once_with('dummy_path', False) # force=False
    mock_output_functions["display_terminal"].assert_called_once()
    mock_output_functions["generate_html"].assert_not_called()

def test_cli_html_output(mock_services, mock_output_functions):
    """Test CLI with --output-format html."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ['-p', 'dummy_path', '--output-format', 'html'])
    
    assert result.exit_code == 0
    assert "<html>Mocked HTML Output</html>" in result.output # Check if HTML printout is there
    mock_services["read_files"].assert_called_once_with('dummy_path', False)
    mock_output_functions["generate_html"].assert_called_once()
    mock_output_functions["display_terminal"].assert_not_called()

def test_cli_help_message():
    """Test if the CLI --help message works."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ['--help'])
    assert result.exit_code == 0
    assert "Usage: main [OPTIONS]" in result.output # 'main' is the function name for click
    assert "Explore credit card bills from C6 in terminal." in result.output

def test_cli_invalid_output_format():
    """Test CLI with an invalid output format."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ['-p', 'dummy_path', '--output-format', 'wrong_format'])
    assert result.exit_code != 0 # Expecting failure
    assert "Invalid value for '--output-format' / '-o'" in result.output # Click's error message

def test_cli_index_option(mock_services, mock_output_functions):
    """Test CLI with --index option."""
    runner = CliRunner()
    # Assume read_files returns a list-like object that can be indexed
    mock_file_item1 = MagicMock()
    mock_file_item1.path.name = "file1.pdf"
    mock_file_item2 = MagicMock()
    mock_file_item2.path.name = "file2.pdf"
    
    mock_files_obj = MagicMock()
    # Make it behave like a list for __getitem__
    mock_files_obj.__getitem__.side_effect = lambda idx: [mock_file_item1, mock_file_item2][idx]
    mock_services["read_files"].return_value = mock_files_obj

    result = runner.invoke(cli_main, ['-p', 'dummy_path', '-i', '2']) # User provides 1-based index
    
    assert result.exit_code == 0
    # Check that the correct file (index 1 because user passes 2) was processed.
    # display_terminal_output is called with keyword arguments.
    kwargs_display_terminal = mock_output_functions["display_terminal"].call_args[1]
    assert kwargs_display_terminal['file'] == mock_file_item2

    # plot_next_months is called with file as the first positional argument.
    pos_args_plot_next = mock_services["plot_next_months"].call_args[0]
    assert pos_args_plot_next[0] == mock_file_item2

# More tests could include: verbose flag, force flag.
# Testing the actual setup() function call might be complex if it has side effects like logging.
# For now, the mocks bypass deep interaction with setup.
