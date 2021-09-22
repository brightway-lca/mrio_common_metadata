import json
from pathlib import Path
import pandas as pd
import numpy as np
import scipy.sparse
import tarfile
from .version_config import VERSIONS
from .datapackage import DATAPACKAGE
from .utils import md5


class Converter():

    sector_columns = ['location', 'sector name', 'sector code 1', 'sector code 2']
    product_columns = ['location', 'product', 'product code 1', 'product code 2', 'unit']

    def __init__(self, sourcedir, targetdir=None, version="3.3.18 hybrid"):

        # sanitize user input: sourcedir must be path
        if not isinstance(sourcedir, Path):
            sourcedir = Path(sourcedir)

        # make sure a valid version was given
        if version not in VERSIONS.keys():
            raise Exception(f"Error: Unsupported version: {self.version}")

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


    def package_all(self, normalize=True):

        # load and convert technosphere, extensions, principal production
        self.convert_principal_production(normalize)
        self.convert_technosphere(normalize)
        self.convert_biosphere(normalize)

        # turn files into one datapackage
        filepath = self.create_package()

        # print and return path of datapackage
        print(f"Datapackage created: {self.targetdir}")
        return filepath


    def create_package(self, file=None, metafile="datapackage.json", flush=True):

        # delete resource from metadata if file not found
        DATAPACKAGE["resources"] = [r for r in DATAPACKAGE["resources"] if (self.targetdir / r["path"]).exists()]

        # create hash for each resource
        for resource in DATAPACKAGE["resources"]:
            resource["hash"] = md5(self.targetdir / resource["path"])

        # export metadata to json
        with open(self.targetdir / metafile, "w") as f:
            json.dump(DATAPACKAGE, f, indent=2, ensure_ascii=False)

        # create tar
        if file is None:
            file = self.targetdir / f"exiobase-{self.version.replace(' ', '-')}.tar"

        # add files to package
        with tarfile.open(file, "w") as tar:
            for pth in self.targetdir.iterdir():
                # add file to tar
                tar.add(self.targetdir / pth, arcname=pth.name)
                # delete file
                if flush is True and pth != file:
                    (self.targetdir / pth).unlink()

        return file


    def convert_principal_production(self, normalize=True):

        # helpers
        meta = VERSIONS[self.version]["production"]
        file = Path(meta["filename"])

        if file.suffix == ".csv":

            # load data
            df = pd.read_csv(self.sourcedir / file, header=list(range(len(meta["column names"])))).T[0]
            df.index.names = meta["column names"]

            # delete zero entries if normalization is wanted
            if normalize is True:
                df = df.replace(0, np.nan).dropna()

            # save converted
            df.to_csv(self.targetdir / meta["save as"], compression="infer")

            # save principal production as well as sectors and products
            self.principal_production = df
            self.sector_order = pd.MultiIndex.from_frame(df.reset_index()[self.sector_columns])
            self.product_order = pd.MultiIndex.from_frame(df.reset_index()[self.product_columns])

        else:
            raise Exception(f"Error: Unsupported file format defined for principal production file: {file}")


    def convert_technosphere(self, normalize=True):

        # helpers
        meta = VERSIONS[self.version]["technosphere"]
        file = Path(meta["filename"])

        # check input
        if file.suffix != ".csv":
            raise Exception(f"Error: Unsupported extension for technosphere input file: {file}")
        if self.principal_production is None:
            raise Exception("Error: Must load principal production vector before technosphere matrix! Call convert_prinicpal_production().")

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
            I = np.eye(*df.shape)
            df = I - df

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
            raise Exception(f"Error: Unsupported output extension for technosphere output file: {outfile}")


    def convert_biosphere(self, normalize=True):

        # helper variables
        meta = VERSIONS[self.version]["extensions"]
        file = self.sourcedir / list(meta.values())[0]["filename"]
        dfs = []
        indices = []

        # check input
        if file.suffix not in [".xlsx", ".xlsb"]:
            raise Exception(f"Error: Unsupported extension for biosphere input file: {file}")
        if self.principal_production is None:
            raise Exception("Error: Must load principal production vector before technosphere matrix! Call convert_prinicpal_production().")

        # read data
        reader = pd.ExcelFile(self.sourcedir / list(meta.values())[0]["filename"])
        for resource in meta.values():
            if not isinstance(resource, dict):
                continue
            df = pd.read_excel(
                reader,
                sheet_name=resource["worksheet"],
                index_col=list(range(len(resource["index names"]))),
                header=list(range(len(resource["column names"]))),
            )
            df.index.names = resource["index names"]
            df.columns.names = resource["column names"]
            dfs.append(df.reset_index())
            indices += resource["index names"]

        # concatenate into one dataframe
        df = pd.concat(dfs, ignore_index=True).set_index(pd.unique(indices).tolist())

        # sort columns
        df = df[self.sector_order]

        # normalize
        if normalize is True:
            df = df / self.principal_production

        # save
        outfile = meta["save as"]
        # as compressed csv
        if ".csv" in outfile:
            df.to_csv(self.targetdir /outfile, compression="infer")
        # other
        else:
            raise Exception(f"Error: Unsupported output extension for biosphere output file: {outfile}")