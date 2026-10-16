"""Satellite crop health / drought indicators (e.g. NDVI). TODO: implement once data-source guidance is provided."""
from datetime import date

import pandas as pd

from .base import Source


class SatelliteSource(Source):
    name = "satellite"

    def fetch(self, start: date, end: date, bbox) -> pd.DataFrame:
        raise NotImplementedError
