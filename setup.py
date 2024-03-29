#! /usr/bin/env python3

from setuptools import setup

setup(
    name="filedb",
    use_scm_version={"local_scheme": "node-and-timestamp"},
    setup_requires=["setuptools_scm"],
    author="HOMEINFO - Digitale Informationssysteme GmbH",
    author_email="<info at homeinfo dot de>",
    maintainer="Richard Neumann",
    maintainer_email="<r dot neumann at homeinfo period de>",
    install_requires=[
        "blessings",
        "flask",
        "mimeutil",
        "peewee",
        "peeweeplus",
        "wsgilib",
    ],
    py_modules=["filedb"],
    data_files=[
        ("/usr/lib/systemd/system", ["filedb-cleanup.service", "filedb-cleanup.timer"])
    ],
    entry_points={
        "console_scripts": [
            "filedb-cleanup = filedb:cleanup",
            "filedb-top = filedb:top",
        ]
    },
    description="Centralized file database.",
)
