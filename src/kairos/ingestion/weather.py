"""Weather ground stations and forecasts. TODO: implement once data-source guidance is provided."""
from datetime import date

import pandas as pd

from .base import Source


class WeatherSource(Source):
    name = "weather"

    def fetch(self, start: date, end: date, bbox) -> pd.DataFrame:
        raise NotImplementedError
