import torch
import json
import pandas as pd
from sklearn.metrics import classification_report

from scripts.build_dataset import create_dataset
from scripts.retrain_ae import recalibrate_ae_thresholds
from models.definitions.autoencoder import construct_model
from inference.inference import categorize_risk

from pathlib import Path
BASE_DIR = Path(__file__).parent

def evaluate_model(manual_eval=False, return_eval=False, construction='', features_benign_path=None, features_malicious_path=None):
    if not Path(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv').exists() or not Path(
            BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_malicious.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    def run_eval(ae=None, features_benign_path=None, features_malicious_path=None, return_eval=False):
        if not ae:
            return

        ae.eval()

        with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
            t = json.load(f)
        thresholds = t['ae']
        binary_threshold = t['ae_binary']

        if features_benign_path is None or features_malicious_path is None:
            features_benign = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv', low_memory=False)
            features_malicious = pd.read_csv(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_malicious.csv', low_memory=False)
        else:
            features_benign = pd.read_csv(features_benign_path, low_memory=False)
            features_malicious = pd.read_csv(features_malicious_path, low_memory=False)
        features = pd.concat([features_benign, features_malicious], ignore_index=True)
        x = create_dataset(features, loader=False)

        with torch.no_grad():
            recon = ae(x)
            error = ((x - recon) ** 2).mean(dim=1)

        y_true = pd.Series([0] * len(features_benign) + [1] * len(features_malicious))
        binary_predictions = (error > binary_threshold).int()
        if not return_eval:
            print(classification_report(y_true, binary_predictions))

        categories = categorize_risk(error, thresholds)
        categorical_eval = ''
        for i, label in enumerate(['normal', 'elevated', 'suspicious', 'severe']):
            mask = categories == i
            if mask.sum() > 0:
                actual_attack_rate = y_true[mask].mean()
                category = f'{label}: {mask.sum()} flows, {actual_attack_rate:.1%} actually malicious'
                categorical_eval += f'{category}\n'
                if not return_eval:
                    print(category)

        if return_eval:
            return y_true, binary_predictions, categorical_eval
        return None

    if manual_eval:
        artifacts = BASE_DIR.parent / 'models' / 'artifacts'
        model_paths = sorted((artifacts/'manual_backups'/f'{construction}_construction').glob('ae_model_*'))
        construction_layers = [int(x) for x in construction.split('_')]
        l1, l2, l3 = construction_layers[1:]

        for path in model_paths:
            print(f'Evaluating {path.stem.replace('ae_model_', '').replace('_', ' ')}\n')
            model = construct_model(l1=l1, l2=l2, l3=l3)
            model.load_state_dict(torch.load(path))
            recalibrate_ae_thresholds(model)
            run_eval(model, features_benign_path=features_benign_path, features_malicious_path=features_malicious_path)

    else:
        if not construction:
            model = construct_model(load=True)
        else:
            construction_layers = [int(x) for x in construction.split('_')]
            l1, l2, l3 = construction_layers[1:]
            model = construct_model(load=True, l1=l1, l2=l2, l3=l3)

        if not Path(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json').exists():
            from scripts.calibrate_thresholds import calibrate_thresholds
            calibrate_thresholds()

        if return_eval:
            return run_eval(model, features_benign_path=features_benign_path, features_malicious_path=features_malicious_path, return_eval=return_eval)
        run_eval(model, features_benign_path=features_benign_path, features_malicious_path=features_malicious_path, return_eval=return_eval)
        return None

if __name__ == '__main__':
    eval = evaluate_model(
        manual_eval=True,
        return_eval=True,
        construction='20_32_16_8',
        features_benign_path=r'C:\Users\lmcau619\Documents\GitHub\NIDS\experiments\final_ae_features.csv',
        features_malicious_path=r'C:\Users\lmcau619\Documents\GitHub\NIDS\experiments\final_ae_features.csv',
    )
    if eval is not None:
        y_pred, binary_predictions, categorical_eval = eval
        print(classification_report(y_pred, binary_predictions))
        print(categorical_eval)