"""On-ground sensors (soil moisture, canopy temp, humidity). TODO: implement once data-source guidance is provided."""
from datetime import date

import pandas as pd

from .base import Source


class SensorsSource(Source):
    name = "sensors"

    def fetch(self, start: date, end: date, bbox) -> pd.DataFrame:
        raise NotImplementedError
