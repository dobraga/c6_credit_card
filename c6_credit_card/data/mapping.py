from json import loads
from pathlib import Path

import pandas as pd

FILE = Path(__file__).parents[0] / "mapping.json"


class Mapping:
    def __init__(self, file: Path = FILE) -> None:
        with open(file) as f:
            _mapping: dict[str, dict[str, list[str]]] = loads(f.read())

        self._mapping = {k: "|".join(v) for k, v in _mapping["mapping"].items()}
        self._rename = {
            k: r"\b({})\b".format("|".join(v)) for k, v in _mapping["rename"].items()
        }

    def __repr__(self) -> str:
        return f"Mapping(mapping={self._mapping}, rename={self._rename})"

    def rename(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data["original"] = data.local.copy()

        for key, regex in self._rename.items():
            mask = data.local.str.contains(regex, case=False, regex=True)
            data.loc[mask, "local"] = key.upper()

        return data

    def classify(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()

        for key, regex in self._mapping.items():
            mask = data.local.str.contains(regex, case=False, regex=True)
            data.loc[mask, "type"] = key

        data["type"] = data["type"].fillna("others")

        return data
