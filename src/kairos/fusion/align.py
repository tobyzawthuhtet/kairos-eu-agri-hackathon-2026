"""Align multi-source data to farm level (spatial join + daily resampling)."""
import pandas as pd


def to_farm_daily(farms: pd.DataFrame, sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return one row per farm per day with columns of DailyObservation. TODO."""
    raise NotImplementedError
