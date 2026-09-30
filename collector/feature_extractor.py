"""
Standardized Feature Extraction Module.
Converts validated telemetry payloads into strictly ordered 2D NumPy arrays
for Scikit-learn Isolation Forest training and real-time inference.
"""

import sys
from pathlib import Path
from typing import Union, Dict, Any, List
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import model_config
from collector.data_validator import TelemetryPayload


class FeatureExtractor:
    """
    Extracts and standardizes numeric feature vectors from validated telemetry.
    Strictly preserves feature column ordering to avoid feature misalignment.
    """

    FEATURE_NAMES: List[str] = list(model_config.feature_columns)

    @classmethod
    def extract_vector(cls, telemetry: Union[TelemetryPayload, Dict[str, Any]]) -> np.ndarray:
        """
        Converts a single telemetry reading into a 2D NumPy feature vector of shape (1, 7).

        Returns:
            np.ndarray of shape (1, 7) with dtype float64.
        """
        if isinstance(telemetry, TelemetryPayload):
            data_dict = telemetry.model_dump()
        elif isinstance(telemetry, dict):
            data_dict = telemetry
        else:
            raise TypeError(f"Expected TelemetryPayload or dict, got {type(telemetry).__name__}")

        values = []
        for feature in cls.FEATURE_NAMES:
            if feature not in data_dict or data_dict[feature] is None:
                raise ValueError(f"Missing required feature '{feature}' in telemetry data")
            values.append(float(data_dict[feature]))

        # Return shape (1, num_features) ready for scikit-learn model.predict() or score_samples()
        return np.array(values, dtype=np.float64).reshape(1, -1)

    @classmethod
    def extract_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts and verifies ordered feature matrix X from a pandas DataFrame.
        Ensures exact column alignment across training and test datasets.
        """
        missing_cols = [col for col in cls.FEATURE_NAMES if col not in df.columns]
        if missing_cols:
            raise ValueError(f"DataFrame missing required feature columns: {missing_cols}")

        return df[cls.FEATURE_NAMES].astype(np.float64)

    @classmethod
    def get_feature_names(cls) -> List[str]:
        """Returns the immutable list of feature names."""
        return cls.FEATURE_NAMES.copy()
