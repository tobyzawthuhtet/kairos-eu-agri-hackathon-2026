import numpy as np
import pandas as pd
import xarray as xr

from kairos.features.era5_features import _deaccumulate, rh_percent


def test_deaccumulate_hourly_increments():
    t = pd.date_range("2022-01-01 00:00", periods=4, freq="h")  # 00,01,02,03
    da = xr.DataArray([5.0, 1.0, 3.0, 6.0], coords={"valid_time": t}, dims="valid_time")
    inc = _deaccumulate(da, "valid_time")
    assert list(inc.values) == [1.0, 2.0, 3.0]  # 01:00 is its own increment, then diffs


def test_rh_saturated_and_dry():
    t = xr.DataArray([20.0, 20.0])
    td = xr.DataArray([20.0, 5.0])
    rh = rh_percent(t, td).values
    assert abs(rh[0] - 100) < 1e-6 and rh[1] < 40
    assert not np.isnan(rh).any()
