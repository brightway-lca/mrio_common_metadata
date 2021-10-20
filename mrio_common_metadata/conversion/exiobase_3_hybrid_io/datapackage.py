DATAPACKAGE = {
    "name": "EXIOBASE 3.3.17 Hybrid",
    "id": "exiobase-3.3.17-hybrid",
    "licenses": [
        {
            "name": "CC-BY-SA-4.0",
            "path": "https://creativecommons.org/licenses/by-sa/4.0/",
            "title": "Creative Commons Attribution Share-Alike 4.0",
        }
    ],
    "description": """The hybrid supply-use and input-output tables of EXOBASE are available for the year 2011. When new data become available the hybrid supply-use and input-output tables may be generated. The latest version can be identified by its version number and its advised to use this latest version. Previous versions will still be available for reference purpose.

References:

* Merciai, Stefano, and Jannick Schmidt. 2016. [Physical/Hybrid Supply and Use Tables. Methodological Report. EU FP7 DESIRE Project](http://fp7desire.eu/documents/category/3-public-deliverables).
* Merciai, Stefano, and Jannick Schmidt. 2018. [Methodology for the Construction of Global Multi-Regional Hybrid Supply and Use Tables for the EXIOBASE v3 Database](https://onlinelibrary.wiley.com/doi/full/10.1111/jiec.12713). Journal of Industrial Ecology 22, no. 3 (2018): 516-31. doi:10.1111/jiec.12713.""",
    "version": "3.3.17",
    "sources": [
        {
            "title": "EXIOBASE raw data download",
            "path": "https://exiobase.eu/index.php/data-download/exiobase3hyb/125-exiobase-3-3-17-hsut-2011",
        }
    ],
    "contributors": [
        {
            "title": "Chris Mutel",
            "email": "cmutel@gmail.com",
            "path": "https://chris.mutel.org/",
            "role": "author",
        },
        {
            "title": "Benjamin W. Portner",
            "email": "benjamin.portner@bauhaus-luftfahrt.net",
            "role": "author",
        },
    ],
    "image": "https://exiobase.eu/images/basisafbeeldingen/ExioBase_Logo_600.png",
    "resources": [
        {
            "name": "extensions",
            "path": "extensions.csv.bz2",
            "profile": "tabular-data-resource",
            "mediatype": "text/csv+bz2",
            "title": "Extension exchange values",
            "format": "csv",
        },
        {
            "name": "production",
            "path": "production.csv.bz2",
            "profile": "tabular-data-resource",
            "mediatype": "text/csv+bz2",
            "title": "Diagonal principal production values",
            "format": "csv",
            "schema": {
                "fields": [
                    {"name": "location"},
                    {"name": "sector name"},
                    {"name": "sector code 1"},
                    {"name": "sector code 2"},
                    {"name": "product name"},
                    {"name": "product code 1"},
                    {"name": "product code 2"},
                    {"name": "unit"},
                    {"name": "value", "type": "number"},
                ]
            },
        },
        # EITHER (writing hiot to csv file)
        {
            "name": "technosphere",
            "path": "technosphere.csv.bz2",
            "profile": "tabular-data-resource",
            "mediatype": "text/csv+bz2",
            "title": "Values from Input-Output table (excluding production)",
            "format": "csv",
        },
        # OR (writing hiot to npz)
        {
            "name": "technosphere",
            "path": "technosphere.npz",
            "profile": "tabular-data-resource",
            "mediatype": "text/csv+bz2",
            "title": "Values from Input-Output table (excluding production)",
            "format": "npz",
        },
    ],
}
