import torch
import pandas as pd

def test_ae_forward_pass():
    """AE should accept 20 features and return 20 features."""
    from models.definitions.autoencoder import construct_model
    model = construct_model(load=False)
    x = torch.randn(5, 20)
    out = model(x)
    assert out.shape == (5, 20)

def test_ae_reconstruction_error_positive():
    from models.definitions.autoencoder import construct_model
    model = construct_model(load=True)
    model.eval()
    x = torch.randn(10, 20)
    with torch.no_grad():
        recon = model(x)
        error = ((x - recon) ** 2).mean(dim=1)
    assert (error >= 0).all(), "Reconstruction error should always be non-negative"

def test_rf_predict_proba_range():
    """RF should output probabilities between 0 and 1."""
    from models.definitions.random_forest import construct_model
    rf = construct_model()
    X_test = pd.read_csv('datasets/processed/rf_testing.csv').head(100)
    proba = rf.predict_proba(X_test)[:, 1]
    assert (proba >= 0).all() and (proba <= 1).all()

def test_categorize_risk():
    from inference.inference import categorize_risk
    import numpy as np
    thresholds = [0.1, 0.3, 0.6]
    scores = np.array([0.05, 0.2, 0.4, 0.8])
    categories = categorize_risk(scores, thresholds)
    assert list(categories) == [0, 1, 2, 3]

def test_calculate_percent_range():
    from inference.inference import calculate_percent, categorize_risk
    import numpy as np
    thresholds = [0.1, 0.3, 0.6]
    max_threshold = 0.9
    scores = np.array([0.05, 0.2, 0.4, 0.8])
    categories = categorize_risk(scores, thresholds)
    percents = calculate_percent(categories, scores, thresholds, max_threshold)
    assert (percents >= 0).all() and (percents <= 100).all()