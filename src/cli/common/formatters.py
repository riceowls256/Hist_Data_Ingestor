"""
Output formatting functions for CLI commands.
"""

import csv
import json
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import List, Dict

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def format_table_output(results: List[Dict], schema: str) -> Table:
    """Format query results as Rich table for console display."""
    table = Table(show_header=True, header_style="bold magenta")

    if not results:
        table.add_column("Message")
        table.add_row("No data found for the specified criteria.")
        return table

    # Add columns based on schema
    if schema.startswith("ohlcv"):
        table.add_column("Symbol")
        table.add_column("Date")
        table.add_column("Open")
        table.add_column("High")
        table.add_column("Low")
        table.add_column("Close")
        table.add_column("Volume")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")).split("T")[0] if row.get("ts_event") else "",
                str(row.get("open_price", "")),
                str(row.get("high_price", "")),
                str(row.get("low_price", "")),
                str(row.get("close_price", "")),
                str(row.get("volume", ""))
            )
    elif schema == "trades":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Price")
        table.add_column("Size")
        table.add_column("Side")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("price", "")),
                str(row.get("size", "")),
                str(row.get("side", ""))
            )
    elif schema == "tbbo":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Bid Price")
        table.add_column("Bid Size")
        table.add_column("Ask Price")
        table.add_column("Ask Size")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("bid_px_00", "")),
                str(row.get("bid_sz_00", "")),
                str(row.get("ask_px_00", "")),
                str(row.get("ask_sz_00", ""))
            )
    elif schema == "statistics":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Stat Type")
        table.add_column("Value")
        table.add_column("Update Action")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("stat_type", "")),
                str(row.get("stat_value", "")),
                str(row.get("update_action", ""))
            )
    elif schema == "definitions":
        table.add_column("Symbol")
        table.add_column("Raw Symbol")
        table.add_column("Asset")
        table.add_column("Exchange")
        table.add_column("Currency")
        table.add_column("Tick Size")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("raw_symbol", "")),
                str(row.get("asset", "")),
                str(row.get("exchange", "")),
                str(row.get("currency", "")),
                str(row.get("tick_size", ""))
            )
    else:
        # Generic table for unknown schemas
        if results:
            for key in results[0].keys():
                table.add_column(key.replace("_", " ").title())

            for row in results:
                table.add_row(*[str(value) for value in row.values()])

    return table


def format_csv_output(results: List[Dict]) -> str:
    """Format query results as CSV string."""
    if not results:
        return ""

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=results[0].keys())
    writer.writeheader()

    for row in results:
        # Handle Decimal and datetime serialization
        serialized_row = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                serialized_row[key] = str(value)
            elif isinstance(value, datetime):
                serialized_row[key] = value.isoformat()
            else:
                serialized_row[key] = value
        writer.writerow(serialized_row)

    return output.getvalue()


def format_json_output(results: List[Dict]) -> str:
    """Format query results as JSON string."""
    def json_serializer(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(results, indent=2, default=json_serializer)


def write_output_file(content: str, file_path: str, format_type: str):
    """Write formatted content to file with proper error handling."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"✅ [green]Output written to {file_path}[/green]")
    except IOError as e:
        console.print(f"❌ [red]Failed to write file {file_path}: {e}[/red]")
        raise typer.Exit(1)