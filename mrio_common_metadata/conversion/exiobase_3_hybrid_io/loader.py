import json
import pandas as pd
from pathlib import Path
import tarfile
import scipy.sparse
from typing import Union
from .datapackage import DATAPACKAGE
from .version_config import VERSIONS


class Loader:

    sector_columns = ["location", "sector name", "sector code 1", "sector code 2"]
    product_columns = [
        "location",
        "product name",
        "product code 1",
        "product code 2",
        "unit",
    ]
    biosphere_columns = ["name", "unit", "compartment"]

    def __init__(
        self, file: Union[str, Path], metafile: str = "datapackage.json"
    ) -> None:

        # check if file is a tar archive
        file = Path(file)
        if file.suffix != ".tar":
            raise Exception(f"Error: Input file must be a tar datapackage. Got {file}.")
        else:
            self.file = file

        # check if file contains metadata
        if metafile not in tarfile.open(self.file).getnames():
            raise Exception(
                f"Error: Datapackage does not contain metadata file {metafile}."
            )
        else:
            self.metafile = metafile
            self.metadata = self.load_metadata()

    def load_metadata(self) -> dict:
        return json.loads(tarfile.open(self.file).extractfile(self.metafile).read())

    def get_resource(self, resource_name: str) -> dict:
        resources = self.metadata["resources"]
        assert len([r for r in resources if r["name"] == resource_name]) == 1
        return next(r for r in resources if r["name"] == resource_name)

    def load_principal_production(self) -> pd.DataFrame:
        resource = self.get_resource("production")
        compression = resource["path"].split(".")[-1]
        index_names = pd.unique(self.sector_columns + self.product_columns).tolist()
        return pd.read_csv(
            tarfile.open(self.file).extractfile(resource["path"]),
            compression=compression,
            index_col=index_names,
        )["0"].rename("principal production")

    def load_technosphere(
        self, as_dataframe=False
    ) -> Union[pd.DataFrame, scipy.sparse.spmatrix]:
        resource = self.get_resource("technosphere")
        index_names = self.product_columns
        column_names = self.sector_columns
        if Path(resource["path"]).suffix == ".npz":
            # load sparse matrix
            technosphere = scipy.sparse.load_npz(
                tarfile.open(self.file).extractfile(resource["path"])
            )
            if as_dataframe is False:
                return technosphere
            # convert to dense matrix and add labels
            else:
                prod = self.load_principal_production().reset_index()
                df = pd.DataFrame(
                    data=technosphere.todense(),
                    index=pd.MultiIndex.from_frame(prod[index_names]),
                    columns=pd.MultiIndex.from_frame(prod[column_names]),
                )
                return df
        elif ".csv" in resource["path"]:
            compression = resource["path"].split(".")[-1]
            df = pd.read_csv(
                tarfile.open(self.file).extractfile(resource["path"]),
                compression=compression,
                index_col=list(range(len(index_names))),
                header=list(range(len(column_names))),
            )
            # df.index.names = index_names
            # df.columns.names = column_names
            return df
        pass

    def load_biosphere(self) -> pd.DataFrame:
        resource = self.get_resource("extensions")
        column_names = self.sector_columns
        index_names = self.biosphere_columns
        compression = resource["path"].split(".")[-1]
        df = pd.read_csv(
            tarfile.open(self.file).extractfile(resource["path"]),
            compression=compression,
            index_col=list(range(len(index_names))),
            header=list(range(len(column_names))),
        )
        return df
