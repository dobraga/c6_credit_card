from datetime import datetime as date
from logging import getLogger
from pathlib import Path
from re import search
from typing import Optional

import pandas as pd

from .file import File
from .mapping import Mapping


class Files:
    def __init__(self, folder: str) -> None:
        self.folder = folder
        self._filenames = [f for f in Path(folder).glob("*.pdf")]
        if not self._filenames:
            raise Exception(f'Not files found into "{self.folder}"')

        months = [_get_date_from_filename(f.name) for f in self._filenames]
        self._files = [File(f, m) for f, m in zip(self._filenames, months)]
        self._files.sort()
        self.last_file = len(self._filenames) - 1

    def process(
        self, password: Optional[str] = None, mapping: Mapping = Mapping(), force=False
    ) -> None:
        LOG.info(mapping)
        [f.process(password, mapping, force) for f in self._files]

    def summary_all(self, by: str = None) -> pd.DataFrame:
        dfs = []
        by_ = ["month"]
        if by:
            by_.append(by)

        for file in self:
            dfs.append(file.summary(by_, add_total=False).data)
        return pd.concat(dfs)

    def __getitem__(self, index=None) -> File:
        if index is None:
            index = self.last_file
        return self._files[index]

    def __len__(self) -> int:
        return len(self._files)

    def __repr__(self) -> str:
        return f"Files(files={self._files})"


def _get_date_from_filename(file: str) -> date:
    if s := search(r"(\d{2})(.)(\d{4})", file):
        month, _, year = s.groups()
    elif s := search(r"(\d{4})(.)(\d{2})", file):
        year, _, month = s.groups()
    else:
        raise Exception("Need two date format on file names %m-%Y or %Y-%m")

    return date(int(year), int(month), 1)


LOG = getLogger(__name__)
