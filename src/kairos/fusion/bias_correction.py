"""Bias-correct model/regional outputs against on-ground sensor observations."""
import pandas as pd


def linear_bias_correct(model: pd.Series, observed: pd.Series) -> pd.Series:
    """Mean-bias adjustment over the overlap period (simple baseline; refine later)."""
    bias = (model - observed).dropna().mean()
    return model - (0.0 if pd.isna(bias) else bias)
