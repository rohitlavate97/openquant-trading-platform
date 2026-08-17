"""Structured Google Sheets and CSV Strategy Signal Parser."""

import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Any

from openquant.domain.models.strategy_sources import (
    SheetsParseResult,
    SheetsSignalType,
    SheetsStrategyRow,
)
from openquant.domain.ports.strategy_sources_port import IStructuredSheetsParser

logger = logging.getLogger(__name__)


class StructuredSheetsParser(IStructuredSheetsParser):
    """Parser validating structured strategy trade rows from CSV / Google Sheet exports."""

    EXPECTED_COLUMNS = {"symbol", "signal_type", "quantity"}

    def validate_row(self, row_data: dict[str, str], row_index: int) -> SheetsStrategyRow:
        """Validate an individual signal row against data types and boundaries."""
        # Normalize header keys to lowercase
        norm_row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row_data.items() if k}

        # Check required columns
        symbol = norm_row.get("symbol", "").upper()
        signal_type_raw = norm_row.get("signal_type", "").upper()
        quantity_raw = norm_row.get("quantity", "")
        timestamp = norm_row.get("timestamp", datetime.now(timezone.utc).isoformat())
        strategy_tag = norm_row.get("strategy_tag", "sheets_signal")

        if not symbol:
            return SheetsStrategyRow(
                row_index=row_index,
                timestamp=timestamp,
                symbol="UNKNOWN",
                signal_type=SheetsSignalType.BUY,
                quantity=Decimal("0"),
                is_valid=False,
                validation_error="Missing required 'symbol' field",
            )

        if signal_type_raw not in {"BUY", "SELL", "CLOSE"}:
            return SheetsStrategyRow(
                row_index=row_index,
                timestamp=timestamp,
                symbol=symbol,
                signal_type=SheetsSignalType.BUY,
                quantity=Decimal("0"),
                is_valid=False,
                validation_error=f"Invalid signal_type '{signal_type_raw}'. Must be BUY, SELL, or CLOSE.",
            )

        try:
            quantity = Decimal(quantity_raw)
            if quantity <= Decimal("0"):
                return SheetsStrategyRow(
                    row_index=row_index,
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=SheetsSignalType(signal_type_raw),
                    quantity=quantity,
                    is_valid=False,
                    validation_error=f"Quantity '{quantity}' must be strictly positive.",
                )
        except (InvalidOperation, ValueError):
            return SheetsStrategyRow(
                row_index=row_index,
                timestamp=timestamp,
                symbol=symbol,
                signal_type=SheetsSignalType(signal_type_raw),
                quantity=Decimal("0"),
                is_valid=False,
                validation_error=f"Invalid numeric quantity: '{quantity_raw}'",
            )

        limit_price = None
        if norm_row.get("limit_price"):
            try:
                limit_price = Decimal(norm_row["limit_price"])
            except Exception:
                pass

        stop_loss = None
        if norm_row.get("stop_loss"):
            try:
                stop_loss = Decimal(norm_row["stop_loss"])
            except Exception:
                pass

        take_profit = None
        if norm_row.get("take_profit"):
            try:
                take_profit = Decimal(norm_row["take_profit"])
            except Exception:
                pass

        return SheetsStrategyRow(
            row_index=row_index,
            timestamp=timestamp,
            symbol=symbol,
            signal_type=SheetsSignalType(signal_type_raw),
            quantity=quantity,
            limit_price=limit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_tag=strategy_tag,
            is_valid=True,
            validation_error=None,
        )

    def parse_csv_content(self, content: str) -> SheetsParseResult:
        """Parse raw CSV or tab-separated string into typed SheetsStrategyRow items."""
        rows: list[SheetsStrategyRow] = []
        parsed_orders: list[dict[str, Any]] = []

        # Auto-detect delimiter (comma or tab)
        delimiter = "\t" if "\t" in content and "," not in content else ","

        reader = csv.DictReader(io.StringIO(content.strip()), delimiter=delimiter)
        for idx, row in enumerate(reader, start=1):
            parsed_row = self.validate_row(row, row_index=idx)
            rows.append(parsed_row)

            if parsed_row.is_valid:
                parsed_orders.append({
                    "symbol": parsed_row.symbol,
                    "side": parsed_row.signal_type.value,
                    "quantity": float(parsed_row.quantity),
                    "limit_price": float(parsed_row.limit_price) if parsed_row.limit_price else None,
                    "strategy_tag": parsed_row.strategy_tag,
                })

        valid_count = sum(1 for r in rows if r.is_valid)
        invalid_count = len(rows) - valid_count

        return SheetsParseResult(
            total_rows=len(rows),
            valid_rows_count=valid_count,
            invalid_rows_count=invalid_count,
            rows=rows,
            parsed_orders=parsed_orders,
        )


# Global singleton sheets parser
structured_sheets_parser = StructuredSheetsParser()
