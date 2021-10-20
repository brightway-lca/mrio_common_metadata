import hashlib
import pandas as pd
from typing import Union
from pathlib import Path


def md5(filepath: Union[str, Path], blocksize: int = 65536):
    """Generate MD5 hash for file at `filepath`"""
    hasher = hashlib.md5()
    fo = open(filepath, "rb")
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()


def append_to_index(df: pd.DataFrame, columns: dict) -> pd.DataFrame:
    index = df.index.to_frame(index=False)
    for k, v in columns.items():
        index[k] = v
    df.index = pd.MultiIndex.from_frame(index)
    return df
