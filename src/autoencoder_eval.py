import torch
import pandas as pd

from utils.build_dataset import create_dataset
from models.autoencoder import construct_model

def evaluate_model(show_error_flag=True):
    model = construct_model()
    model.eval()

    THRESHOLD = 0.113147736

    def show_error(X, label, expected: int):
        with torch.no_grad():
            recon = model(X)
            error = ((X - recon) ** 2).mean(dim=1)

            guesses = error > THRESHOLD
            correct, wrong = 0, 0
            for guess in guesses:
                if guess == expected:
                    correct += 1
                    continue
                wrong += 1

            out = error.mean().item()
            print(f'{label}: {round(out * 100, 1)}% total reconstruction error, expected {100 if expected else 0}%')
            return correct, wrong

    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[1]

    features_benign = pd.read_csv(f'{BASE_DIR}/datasets/processed/ae_testing_benign.csv', low_memory=False)
    X_benign = create_dataset(features_benign, loader=False)
    recon = model(X_benign)
    error = ((X_benign - recon) ** 2).mean(dim=1)
    print("Validation error stats:",
          error.min(),
          error.mean(),
          error.max())

    if show_error_flag:
        features_malicious = pd.read_csv(f'{BASE_DIR}/datasets/processed/ae_testing_malicious.csv', low_memory=False)
        X_malicious = create_dataset(features_malicious, loader=False)

        true_pos, false_neg = show_error(X_malicious, 'Malicious', True)
        true_neg, false_pos = show_error(X_benign, 'Benign', False)

        print(f'\nRecall: {round((true_pos / (true_pos + false_neg)) * 100, 2)}%, Precision: {round((true_pos / (true_pos + false_pos)) * 100, 2)}%')
        return None

    return error

evaluate_model()