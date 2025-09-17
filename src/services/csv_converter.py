"""
CSV conversion utilities module.
Converts JSON data structures to CSV format for Mirakl API integration.
"""

import io
import csv
import logging
from logs.config_logs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def make_csv(data):
    """
    Converts JSON (dict | list[dict]) → CSV (string in memory).
    """
    if not data:  # empty value
        logger.warning("make_csv received empty data")
        return ""

    output = io.StringIO()

    # Determine list of dictionaries
    rows = data if isinstance(data, list) else [data]

    # Collect all keys (in case of heterogeneous dictionaries)
    fieldnames = set()
    for row in rows:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Expected dict, but got: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    # Get id/ean from first row (if available)
    first = rows[0]
    logger.info(
        f"Converted to CSV with product-id: {first.get('product-id')}, ean: {first.get('ean')}"
    )

    return output.getvalue()


def make_big_csv(data):
    """
    Converts list of JSON objects → CSV (string in memory).
    """
    if not data or not isinstance(data, list):
        logger.error("make_big_csv received empty or invalid data")
        return ""

    output = io.StringIO()

    # Collect all keys (in case of heterogeneous dictionaries)
    fieldnames = set()
    for row in data:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Expected dict, but got: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        writer.writerow(row)
        
    
    eans = [row.get("ean") for row in data if row.get("ean")]
    logger.info(
        f"Converted big CSV with eans: {eans}"
    )

    return output.getvalue()
