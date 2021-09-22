from .version import version as __version__

__all__ = ("get_metadata_resource", "get_numeric_data_iterator", "list_resources")

from .utils import load_compressed_csv, iterate_compressed_csv
from pathlib import Path
import json
import tarfile
import scipy.sparse


def _get_valid_dirpath(dirpath):
    metafile = "datapackage.json"
    dirpath = Path(dirpath)
    # check if it contains metadata file
    # if given a directory
    if dirpath.is_dir():
        assert (dirpath / metafile).is_file()
    # if given a tar archive
    elif dirpath.is_file() and dirpath.suffix == '.tar':
        assert metafile in tarfile.open(dirpath).getnames()
    else:
        assert (dirpath / "datapackage.json").is_file()
    return dirpath


def _get_resources(dirpath):
    dirpath = _get_valid_dirpath(dirpath)
    return json.load(open(dirpath / "datapackage.json"))["resources"]


def _get_resource(dirpath, resource_name):
    resources = _get_resources(dirpath)
    assert len([r for r in resources if r["name"] == resource_name]) == 1
    return next(r for r in resources if r["name"] == resource_name)


def list_resources(dirpath):
    return [resource["name"] for resource in _get_resources(dirpath)]


def get_metadata_resource(dirpath, resource_name):
    resource = _get_resource(dirpath, resource_name)
    names = [f["name"] for f in resource["schema"]["fields"]]
    data = load_compressed_csv(Path(dirpath) / resource["path"])
    return [dict(zip(names, row)) for row in data]


def _get_foreign_key(dirpath, resource, field):
    fk = next(fk for fk in resource["foreignKeys"] if fk["fields"] == field)
    return (
        fk["reference"]["fields"],
        _get_resource(dirpath, fk["reference"]["resource"]),
    )


def get_numeric_data_iterator(dirpath, resource_name):
    resource = _get_resource(dirpath, resource_name)

    assert len(resource["foreignKeys"]) == 2

    row_id_field, row_resource = _get_foreign_key(
        dirpath, resource, resource["schema"]["fields"][0]["name"]
    )
    row_mapping = {
        elem[row_id_field]: elem
        for elem in get_metadata_resource(dirpath, row_resource["name"])
    }

    col_id_field, col_resource = _get_foreign_key(
        dirpath, resource, resource["schema"]["fields"][1]["name"]
    )
    col_mapping = {
        elem[col_id_field]: elem
        for elem in get_metadata_resource(dirpath, col_resource["name"])
    }

    for row, col, value in iterate_compressed_csv(Path(dirpath) / resource["path"]):
        yield row_mapping[row], col_mapping[col], float(value)
