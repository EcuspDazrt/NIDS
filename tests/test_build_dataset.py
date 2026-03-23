# tests/test_build_dataset.py
import pandas as pd
import numpy as np
from pathlib import Path


def test_scaler_exists_after_training():
    path = Path('models/artifacts/ae_scaler.pkl')
    assert path.exists(), "AE scaler not found — run ae_train.py first"


def test_scaler_column_count():
    import joblib
    scaler = joblib.load('models/artifacts/ae_scaler.pkl')
    assert len(scaler.feature_names_in_) == 20, \
        f"Expected 20 features, got {len(scaler.feature_names_in_)}"


def test_create_dataset_transform_consistent():
    """Same input should produce same output on repeated calls."""
    from scripts.build_dataset import create_dataset

    df = pd.DataFrame({col: np.random.rand(10)
                       for col in ['Duration', 'In/Out Ratio', 'Absolute Difference',
                                   'Byte Rate Asymmetry', 'Forward Packet Rate',
                                   'Forward Byte Rate', 'Forward Byte Mean',
                                   'Forward Byte Std', 'Backward Packet Rate',
                                   'Backward Byte Rate', 'Backward Byte Mean',
                                   'Backward Byte Std', 'Forward IAT Mean',
                                   'Forward IAT Std', 'Backward IAT Mean',
                                   'Backward IAT Std', 'Active Mean', 'Active Std',
                                   'Idle Mean', 'Idle Std']})

    x1 = create_dataset(df, loader=False, update_scaler=False)
    x2 = create_dataset(df, loader=False, update_scaler=False)

    import torch
    assert torch.allclose(x1, x2), "Dataset creation not deterministic"