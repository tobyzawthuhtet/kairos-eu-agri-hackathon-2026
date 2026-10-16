"""Common interface for all data sources (sensors, satellite, weather, climate)."""
from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class Source(ABC):
    name: str

    @abstractmethod
    def fetch(self, start: date, end: date, bbox: tuple[float, float, float, float]) -> pd.DataFrame:
        """Download/read raw data for the period; return a tidy DataFrame."""
