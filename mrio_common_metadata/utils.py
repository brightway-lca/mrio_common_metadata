import bz2
import csv
import hashlib


def md5(filepath, blocksize=65536):
    """Generate MD5 hash for file at `filepath`"""
    hasher = hashlib.md5()
    fo = open(filepath, "rb")
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()


def load_compressed_csv(filepath):
    with bz2.open(filepath, "rt") as compressed:
        data = list(csv.reader(compressed))
    return data


def iterate_compressed_csv(filepath):
    with bz2.open(filepath, "rt") as compressed:
        for row in csv.reader(compressed):
            yield row
