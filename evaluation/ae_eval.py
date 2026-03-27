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

def evaluate_model(manual_eval=False, construction=''):
    if not Path(BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_benign.csv').exists() or not Path(
            BASE_DIR.parent / 'datasets' / 'processed' / 'ae_testing_malicious.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    def run_eval(ae=None):
        if not ae:
            return

        ae.eval()

        with open(BASE_DIR.parent/'models'/'artifacts'/'thresholds.json') as f:
            t = json.load(f)
        thresholds = t['ae']
        binary_threshold = t['ae_binary']

        features_benign = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_benign.csv', low_memory=False)
        features_malicious = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_testing_malicious.csv', low_memory=False)
        features = pd.concat([features_benign, features_malicious], ignore_index=True)
        x = create_dataset(features, loader=False)

        with torch.no_grad():
            recon = ae(x)
            error = ((x - recon) ** 2).mean(dim=1)

        y_true = pd.Series([0] * len(features_benign) + [1] * len(features_malicious))
        binary_predictions = (error > binary_threshold).int()
        print(classification_report(y_true, binary_predictions))

        categories = categorize_risk(error, thresholds)
        for i, label in enumerate(['normal', 'elevated', 'suspicious', 'severe']):
            mask = categories == i
            if mask.sum() > 0:
                actual_attack_rate = y_true[mask].mean()
                print(f'{label}: {mask.sum()} flows, {actual_attack_rate:.1%} actually malicious')

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
            run_eval(model)

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

        run_eval(model)

if __name__ == '__main__':
    evaluate_model(
        manual_eval=False,
        construction='20_32_16_8'
    )