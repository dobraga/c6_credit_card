from collections import OrderedDict
from datetime import datetime as date
from logging import getLogger
from pathlib import Path
from typing import Optional, Union

import pandas as pd
from tabula.io import read_pdf

from .mapping import Mapping
from .result import Result


class File:
    def __init__(self, file: Path, month: date) -> None:
        self.file = file
        self.month = month
        self.__cache_file = self.file.with_suffix(".cache")

    def process(
        self, password: Optional[str] = None, mapping: Mapping = Mapping(), force=False
    ) -> None:
        if Path(self.__cache_file).is_file() and not force:
            LOG.debug(f"Reading from cache {self}")
            self._df = pd.read_parquet(self.__cache_file)
        else:
            LOG.debug(f"Processing {self}")
            self._df = _extract(self.file, password).assign(month=self.month)
            self._df.to_parquet(self.__cache_file)
            LOG.debug(f"Processed {self}")

        self._df["local"] = self._df["local"].apply(_minimize_name)
        self._classify(mapping)

    def __repr__(self) -> str:
        return f'File(file="{self.file}")'

    def summary(self, by: Union[str, list[str]], add_total=True) -> Result:
        data = self._df.copy()
        agg = (
            data.groupby(by)
            .agg(qtd=("valor", "count"), tot_value=("valor", "sum"))
            .sort_values("tot_value", ascending=False)
        )

        if add_total:
            data[by] = "total"
            agg_tot = data.groupby(by).agg(
                qtd=("valor", "count"), tot_value=("valor", "sum")
            )
            agg = pd.concat([agg, agg_tot], axis=0)

        return Result(agg.round(2).reset_index())

    def select(self, **kwargs) -> Result:
        data: pd.DataFrame = self._df.copy()

        LOG.debug(f"creating filter with: {kwargs}")

        filters = []
        for field, parameter in kwargs.items():
            if isinstance(parameter, list):
                filters.append(f"{field}.isin({parameter})")
            elif isinstance(parameter, str):
                if ">" in parameter or "<" in parameter or "!=" in parameter:
                    filters.append(f"{field}{parameter}")
                else:
                    filters.append(f'{field} == "{parameter}"')
            else:
                filters.append(f"{field} == {parameter}")

        query = " and ".join(filters)
        LOG.debug(query)

        data = data.query(query).sort_values("valor", ascending=False)

        return Result(data)

    def _classify(self, mapping: Mapping):
        self._df = (
            self._df.pipe(mapping.rename)
            .pipe(mapping.classify)
            .query('type != "remove"')
        )

    def __gt__(self, other) -> bool:
        return self.month > other.month

    def __lt__(self, other) -> bool:
        return self.month < other.month

    def __ge__(self, other) -> bool:
        return self.month >= other.month

    def __le__(self, other) -> bool:
        return self.month <= other.month


def _extract(file: Path, password: Optional[str] = None) -> pd.DataFrame:
    dfs = read_pdf(file, password=password, pages="all", silent=True)
    dfs = [_process_fatura(df) for df in dfs[1:-1]]
    df = pd.concat(dfs, axis=0).drop(columns=["delete"])

    df.valor = df.valor.str.replace(".", "", regex=False).str.replace(
        ",", ".", regex=False
    )
    df = df.query('not valor.str.contains("Unnamed")')
    df.valor = df.valor.astype(float)

    df.data = (
        df.data.str.replace("jan", "01", regex=False)
        .str.replace("fev", "02", regex=False)
        .str.replace("mar", "03", regex=False)
        .str.replace("abr", "04", regex=False)
        .str.replace("mai", "05", regex=False)
        .str.replace("jun", "06", regex=False)
        .str.replace("jul", "07", regex=False)
        .str.replace("ago", "08", regex=False)
        .str.replace("set", "09", regex=False)
        .str.replace("out", "10", regex=False)
        .str.replace("nov", "11", regex=False)
        .str.replace("dez", "12", regex=False)
    )

    df.data = pd.to_datetime(
        df.data + " " + date.today().strftime("%Y"), format="%d %m %Y"
    )

    mask_estorno = df.local.str.contains("Estorno")
    df.loc[mask_estorno, "valor"] = -df.loc[mask_estorno, "valor"]

    parcelas = df.local.str.split(" - Parcela").str[1].str.split("/")
    df["parcela"] = pd.to_numeric(parcelas.str[0], errors="coerce")
    df["parcelas_totais"] = pd.to_numeric(parcelas.str[1], errors="coerce")
    df["parcelas_faltantes"] = df["parcelas_totais"] - df["parcela"]
    c = ["parcela", "parcelas_totais", "parcelas_faltantes"]
    df[c] = df[c].fillna(0).astype(int)

    df["local"] = (
        df["local"]
        .str.replace(r"[^ A-Za-z0-9]", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
    )

    return df


def _process_fatura(fatura: pd.DataFrame):
    if fatura.shape[1] != 4:
        return pd.DataFrame()

    columns = ["data", "local", "delete", "valor"]
    first_row = pd.DataFrame(fatura.columns).T
    fatura.columns = columns
    first_row.columns = columns

    return pd.concat([first_row, fatura], axis=0)


def _minimize_name(name: str) -> str:
    names = name.upper().split(" ")
    names = filter(lambda x: x not in STOPWORDS, names)
    names = list(filter(lambda x: len(x) > 1 and not x.isnumeric(), names))[:2]
    name = " ".join(OrderedDict.fromkeys(names))
    name = name.replace(" Parcela", "")
    return name


STOPWORDS = ["DO", "DA", "DE", "COM", "PARCELA", "BR"]
LOG = getLogger(__name__)
