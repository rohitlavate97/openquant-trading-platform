"""Unit tests for Structured Google Sheets and CSV strategy parser."""

from openquant.adapters.sources.sheets_parser import StructuredSheetsParser


def test_structured_sheets_parser_valid_csv():
    parser = StructuredSheetsParser()
    csv_data = """Timestamp,Symbol,Signal_Type,Quantity,Limit_Price,Stop_Loss,Take_Profit,Strategy_Tag
2026-08-17T10:00:00Z,AAPL,BUY,100,150.50,145.00,160.00,trend_follow
2026-08-17T10:05:00Z,MSFT,SELL,50,300.00,310.00,285.00,mean_revert
"""
    result = parser.parse_csv_content(csv_data)
    assert result.total_rows == 2
    assert result.valid_rows_count == 2
    assert result.invalid_rows_count == 0
    assert len(result.parsed_orders) == 2
    assert result.parsed_orders[0]["symbol"] == "AAPL"
    assert result.parsed_orders[0]["side"] == "BUY"


def test_structured_sheets_parser_invalid_rows():
    parser = StructuredSheetsParser()
    csv_data = """Timestamp,Symbol,Signal_Type,Quantity
2026-08-17T10:00:00Z,,BUY,100
2026-08-17T10:05:00Z,TSLA,INVALID_SIDE,50
2026-08-17T10:10:00Z,NVDA,BUY,-25
2026-08-17T10:15:00Z,AMD,BUY,abc
"""
    result = parser.parse_csv_content(csv_data)
    assert result.total_rows == 4
    assert result.valid_rows_count == 0
    assert result.invalid_rows_count == 4
    assert len(result.rows) == 4
    assert "Missing required 'symbol'" in (result.rows[0].validation_error or "")
    assert "Invalid signal_type" in (result.rows[1].validation_error or "")
    assert "strictly positive" in (result.rows[2].validation_error or "")
    assert "Invalid numeric quantity" in (result.rows[3].validation_error or "")
