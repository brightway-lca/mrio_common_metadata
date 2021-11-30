import json
import pandas as pd
from pathlib import Path
import tarfile
import scipy.sparse
from typing import Union, List
from .version_config import VERSIONS


class Loader:

    biosphere_columns = ["name", "unit", "compartment", "type"]
    flip_sign_extensions = [
        "emission",
        "unregistered waste emission",
        "waste supply",
        "packaging supply",
        "machinery supply",
        "stock addition",
        # "other supply/use",
    ]

    def __init__(
        self,
        file: Union[str, Path],
        metafile: str = "datapackage.json",
        version: str = "3.3.18 hybrid",
    ) -> None:

        # save inputs
        self.file = file
        self.metafile = metafile
        self.version = version

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

        # update column names
        self.sector_columns = VERSIONS[self.version]["technosphere"]["column names"]
        self.product_columns = VERSIONS[self.version]["technosphere"]["index names"]
        self.principal_production_columns = VERSIONS[self.version]["production"][
            "column names"
        ]

    def load_metadata(self) -> dict:
        return json.loads(tarfile.open(self.file).extractfile(self.metafile).read())

    def get_resource(self, resource_name: str) -> dict:
        resources = self.metadata["resources"]
        assert len([r for r in resources if r["name"] == resource_name]) == 1
        return next(r for r in resources if r["name"] == resource_name)

    def load_principal_production(
        self, add_product_location_col: bool = False
    ) -> pd.DataFrame:
        resource = self.get_resource("production")
        compression = resource["path"].split(".")[-1]
        index_names = self.principal_production_columns
        df = pd.read_csv(
            tarfile.open(self.file).extractfile(resource["path"]),
            compression=compression,
            index_col=index_names,
        )["value"].rename("principal production")
        if add_product_location_col is True:
            df = df.to_frame()
            df["product location"] = df.index.get_level_values("sector location")
            df = df.set_index("product location", append=True)[df.columns[0]]
        return df

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
                prod = self.load_principal_production(
                    add_product_location_col=True
                ).reset_index()
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

    def load_biosphere(self, flip_signs: bool = False) -> pd.DataFrame:
        return self.load_extensions(
            use_types=["resource", "land use", "emission"],
            flip_signs=flip_signs,
        )

    def load_extensions(
        self,
        use_types: Union[None, List[str]] = None,
        flip_signs: bool = False,
    ) -> pd.DataFrame:

        # get metadata
        resource = self.get_resource("extensions")
        column_names = self.sector_columns
        index_names = self.biosphere_columns

        # load data
        compression = resource["path"].split(".")[-1]
        df = pd.read_csv(
            tarfile.open(self.file).extractfile(resource["path"]),
            compression=compression,
            index_col=list(range(len(index_names))),
            header=list(range(len(column_names))),
        )

        # flip signs: all outputs are negative, all inputs are positive
        if flip_signs:
            lines = df.query(f"type in {self.flip_sign_extensions}").index
            df.loc[lines, :] = df.loc[lines, :] * -1
            # "other supply/use" contains both supply and use -> treat separately
            lines = df.query(
                f"type == 'other supply/use' & name.str.contains('supply')"
            ).index
            df.loc[lines, :] = df.loc[lines, :] * -1

        # filter extension types
        if use_types is not None:
            df = df.query(f"type in {use_types}")

        return df
