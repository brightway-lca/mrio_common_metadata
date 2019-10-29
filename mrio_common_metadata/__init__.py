__version__ = (0, 1)

__all__ = ("get_labels", "get_data_iterator", "get_resource_metadata", "get_datapackage")


from pathlib import Path
import bz2
import csv
import itertools
import tarfile
import json

DATA_DIR = Path(__file__, "..").resolve() / "data"
DATA_DIR.mkdir(mode=0o777, exist_ok=True)


class MissingDataPackage(Exception):
    pass


def _get_dir(label_or_filepath):
    if (DATA_DIR / label_or_filepath).isdir():
        return DATA_DIR / label_or_filepath
    else:
        dp = Path(label_or_filepath)
        if not dp.isdir():
            raise ValueError(f"{label_or_filepath} is not a recognized table or directory path")
        return dp


def get_datapackage(label_or_filepath):
    """Load the contents of ``datapackage.json`` from a relative or absolute directory path"""
    dp = _get_dir(label_or_filepath)
    try:
        return (dp, json.load(open(dp / "datapackage.json")))
    except OSError:
        raise MissingDataPackage(f"{label_or_filepath} is a directory, but `datapackage.json` is missing")


def check_resources_integrity(label_or_filepath):
    dp, resources = get_datapackage(label_or_filepath)
    # TODO


def check_resources_sentinel_values(label_or_filepath):
    pass
    # TODO


def get_unique_resource(label_or_filepath, resource_name):
    dp, resources = get_datapackage(label_or_filepath)
    resource_possibilities = [o for o in resources if o['name'] == resource_name]

    if not resource_possibilities:
        raise ValueError(f"`{resource_name}` not found in this datapackage")
    elif len(resource_possibilities) > 1:
        raise ValueError(f"`{resource_name}` not unique in this datapackage")
    else:
        return dp, resource_possibilities[0]


def get_labels(label_or_filepath, resource_name):
    """Get row and column labels in the order used in this resource.

    We do both at once to avoid loading the file twice."""
    dp, resource = get_unique_resource(label_or_filepath, resource_name)

    assert resource['mediatype'] == "text/csv+bz2"

    row_raw, col_raw = [], []
    rows_to_capture = max([field.get("row-index", 0) for field in itertools.chain(resource['schema']['rows'], resource['schema']['cols'])])
    cols_to_capture = max([field.get("col-index", 0) for field in itertools.chain(resource['schema']['rows'], resource['schema']['cols'])])

    with bz2.open(dp / resource['path'], "rt") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):



    row_offset_guess, col_offset_guess = get_offsets(filepath)
    if row_offset is None:
        row_offset = row_offset_guess
    if col_offset is None:
        col_offset = col_offset_guess


    with bz2.open(filepath, "rt") as f:
        reader = csv.reader(f)
        col_labels = list(
            itertools.zip_longest(
                *[row[col_offset:] for _, row in zip(range(row_offset), reader)]
            )
        )
        row_labels = [row[:col_offset] for row in reader]

    return row_labels, col_labels


def get_data_iterator(label_or_filepath, resource_name, fill_missing=None):
    with bz2.open(filepath, "rt") as f:
        for i, row in enumerate(csv.reader(f)):
            for j, value in enumerate(row):
                if i >= row_offset and j >= col_offset and value:
                    if float(value) == 0:
                    yield (i - row_offset, j - col_offset, float(value))
