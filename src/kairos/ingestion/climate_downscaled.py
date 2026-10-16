"""Open downscaled climate datasets. TODO: implement once data-source guidance is provided."""
from datetime import date

import pandas as pd

from .base import Source


class ClimateDownscaledSource(Source):
    name = "climate_downscaled"

    def fetch(self, start: date, end: date, bbox) -> pd.DataFrame:
        raise NotImplementedError
