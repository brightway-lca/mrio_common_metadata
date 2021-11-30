import json
from pathlib import Path
import pandas as pd
import numpy as np
import scipy.sparse
import tarfile
from .version_config import VERSIONS
from .datapackage import DATAPACKAGE
from .utils import md5, append_to_index
from typing import Union


# add helper function to append new columns to pandas multiindex
pd.DataFrame.append_to_index = append_to_index


class Converter:
    def __init__(
        self,
        sourcedir: Union[str, Path],
        targetdir: Union[None, str, Path] = None,
        version: str = "3.3.18 hybrid",
    ) -> None:

        # sanitize user input: sourcedir must be path
        if not isinstance(sourcedir, Path):
            sourcedir = Path(sourcedir)

        # make sure a valid version was given
        if version not in VERSIONS.keys():
            raise Exception(f"Error: Unsupported version: {version}")

        # default target directory = source directory/datapackage
        if targetdir is None:
            self.targetdir = sourcedir / "datapackage"
            self.targetdir.mkdir(exist_ok=True)
        else:
            self.targetdir = targetdir

        self.sourcedir = sourcedir
        self.version = version

        self.principal_production = None
        self.sector_order = None
        self.product_order = None

    def package_all(self, normalize: bool = True):

        # update sector and product columns names
        self.sector_columns = VERSIONS[self.version]["technosphere"]["column names"]
        self.product_columns = VERSIONS[self.version]["technosphere"]["index names"]
        self.principal_production_columns = VERSIONS[self.version]["production"][
            "column names"
        ]

        # load and convert technosphere, extensions, principal production
        self.convert_principal_production(normalize)
        self.convert_technosphere(normalize)
        self.convert_extensions(normalize)

        # turn files into one datapackage
        filepath = self.create_package()

        # print and return path of datapackage
        print(f"Datapackage created: {self.targetdir}")
        return filepath

    def create_package(
        self,
        file: Union[None, str, Path] = None,
        metafile: str = "datapackage.json",
        flush: bool = True,
    ) -> Path:

        # delete resource from metadata if file not found
        DATAPACKAGE["resources"] = [
            r for r in DATAPACKAGE["resources"] if (self.targetdir / r["path"]).exists()
        ]

        # create hash for each resource
        for resource in DATAPACKAGE["resources"]:
            resource["hash"] = md5(self.targetdir / resource["path"])

        # export metadata to json
        with open(self.targetdir / metafile, "w") as f:
            json.dump(DATAPACKAGE, f, indent=2, ensure_ascii=False)

        # create tar
        if file is None:
            file = self.targetdir / f"exiobase-{self.version.replace(' ', '-')}.tar"
        elif isinstance(file, str):
            file = Path(file)

        # add files to package
        with tarfile.open(file, "w") as tar:
            for pth in self.targetdir.iterdir():
                # add file to tar
                tar.add(self.targetdir / pth, arcname=pth.name)
                # delete file
                if flush is True and pth != file:
                    (self.targetdir / pth).unlink()

        return file

    def convert_principal_production(self, normalize: bool = True) -> None:

        # helpers
        meta = VERSIONS[self.version]["production"]
        file = Path(meta["filename"])

        if file.suffix == ".csv":

            # load data
            df = (
                pd.read_csv(
                    self.sourcedir / file, header=list(range(len(meta["column names"])))
                )
                .T[0]
                .rename("value")
            )
            df.index.names = meta["column names"]

            # delete zero entries if normalization is wanted
            if normalize is True:
                df = df.replace(0, np.nan).dropna()

            # save converted
            df.to_csv(self.targetdir / meta["save as"], compression="infer")

            # add product location by duplicating sector locations
            # necessary to get correct self.product_order in the next step
            if (
                "product location" not in df.index.names
                and "product location" in self.product_columns
            ):
                df = df.to_frame()
                df["product location"] = df.index.get_level_values("sector location")
                df = df.set_index("product location", append=True)[df.columns[0]]

            # save principal production as well as sectors and products
            self.principal_production = df
            self.sector_order = pd.MultiIndex.from_frame(
                df.reset_index()[self.sector_columns]
            )
            self.product_order = pd.MultiIndex.from_frame(
                df.reset_index()[self.product_columns]
            )

        else:
            raise Exception(
                f"Error: Unsupported file format defined for principal production file: {file}"
            )

    def convert_technosphere(self, normalize: bool = True) -> None:

        # helpers
        meta = VERSIONS[self.version]["technosphere"]
        file = Path(meta["filename"])

        # check input
        if file.suffix != ".csv":
            raise Exception(
                f"Error: Unsupported extension for technosphere input file: {file}"
            )
        if self.principal_production is None:
            raise Exception(
                "Error: Must load principal production vector before technosphere "
                "matrix! Call convert_prinicpal_production()."
            )

        # read data
        df = pd.read_csv(
            self.sourcedir / file,
            index_col=list(range(len(meta["index names"]))),
            header=list(range(len(meta["column names"]))),
        )
        df.index.names = meta["index names"]
        df.columns.names = meta["column names"]

        # make sure columns and rows are given in the same order as in principal production vector
        df = df.loc[self.product_order, self.sector_order]

        # normalize
        if normalize is True:
            df = df / self.principal_production
            df = np.eye(*df.shape) - df

        # save
        # as sparse array
        outfile = Path(meta["save as"])
        if outfile.suffix == ".npz":
            sparse_matrix = scipy.sparse.coo_matrix(df.values)
            scipy.sparse.save_npz(self.targetdir / outfile, sparse_matrix)
        # as compressed csv
        elif ".csv" in outfile:
            df.to_csv(self.targetdir / outfile, compression="infer")
        # other
        else:
            raise Exception(
                f"Error: Unsupported output extension for technosphere output file: {outfile}"
            )

    def convert_extensions(self, normalize: bool = True) -> None:

        # helper variables
        meta = VERSIONS[self.version]["extensions"]
        file = self.sourcedir / list(meta["sheets"].values())[0]["filename"]
        dfs = []
        indices = []

        # check input
        if file.suffix not in [".xlsx", ".xlsb"]:
            raise Exception(
                f"Error: Unsupported extension for biosphere input file: {file}"
            )
        if self.principal_production is None:
            raise Exception(
                "Error: Must load principal production vector before technosphere "
                "matrix! Call convert_prinicpal_production()."
            )

        # read data
        reader = pd.ExcelFile(file)
        for res_name, resource in meta["sheets"].items():
            if not isinstance(resource, dict):
                continue
            df = pd.read_excel(
                reader,
                sheet_name=resource["worksheet"],
                index_col=list(range(len(resource["index names"]))),
                header=list(range(len(meta["column names"]))),
            )
            df.index.names = resource["index names"]
            df.columns.names = meta["column names"]
            df.append_to_index({"type": res_name})
            dfs.append(df.reset_index())
            indices += resource["index names"]

        # concatenate into one dataframe
        df = pd.concat(dfs, ignore_index=True).set_index(
            pd.unique(indices).tolist() + ["type"]
        )

        # sort columns
        df = df[self.sector_order]

        # normalize
        if normalize is True:
            df = df / self.principal_production

        # save
        outfile = meta["save as"]
        # as compressed csv
        if ".csv" in outfile:
            df.to_csv(self.targetdir / outfile, compression="infer")
        # other
        else:
            raise Exception(
                f"Error: Unsupported output extension for biosphere output file: {outfile}"
            )
