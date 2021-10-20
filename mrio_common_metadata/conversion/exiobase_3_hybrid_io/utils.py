import hashlib
import pandas as pd


def md5(filepath, blocksize=65536):
    """Generate MD5 hash for file at `filepath`"""
    hasher = hashlib.md5()
    fo = open(filepath, "rb")
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()

def append_to_index(df, columns):
    index = df.index.to_frame(index=False)
    for k,v in columns.items():
        index[k] = v
    df.index = pd.MultiIndex.from_frame(index)
    return df
