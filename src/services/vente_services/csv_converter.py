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

def make_csv(data: dict):
    """
    Converts a JSON object or list of JSON objects into a CSV string.

    The function accepts either a single dictionary or a list of dictionaries,
    determines the field names dynamically (to support heterogeneous structures),
    and writes the data into an in-memory CSV string.

    Args:
        data (dict | list[dict]): Input JSON data.

    Returns:
        str: CSV representation of the data as a string. Returns an empty string if input is invalid.

    Raises:
        None explicitly, but logs an error if non-dict objects are encountered.
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

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
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
    Converts a list of JSON objects into a CSV string.

    Unlike `make_csv`, this function only accepts a list of dictionaries.
    It collects all keys across the list to support heterogeneous data structures
    and writes the data into an in-memory CSV string.

    Args:
        data (list[dict]): List of JSON objects.

    Returns:
        str: CSV representation of the data as a string. Returns an empty string if input is invalid.

    Raises:
        None explicitly, but logs an error if non-dict objects are encountered.
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

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for row in data:
        writer.writerow(row)
        
    
    eans = [row.get("ean") for row in data if row.get("ean")]
    logger.info(
        f"Converted big CSV with eans: {eans}"
    )

    return output.getvalue()
