import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import shutil
import random

from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

def train_model(load=False, epochs=20, features=None, batch_size=2048, update_scaler=False, save_backup=False, backup_interval=None, label='', construction=''):
    # check if training dataset exists, create it if not
    if not Path(BASE_DIR.parent/'datasets'/'processed'/'ae_training.csv').exists():
        from features.extract_training import process_raw_dataset
        process_raw_dataset()

    print('Training auto-encoder...')

    # create dataset
    if features is None:
        features = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_training.csv', low_memory=False)

    x_train = create_dataset(features, batch_size, update_scaler=update_scaler)

    # construct model
    model = construct_model(load=load)
    criterion = nn.MSELoss(reduction='mean')
    optimizer = optim.Adam(model.parameters(), lr=3e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-6)

    losses = []
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        num_batches = 0
        for batch in x_train:
            x_batch = batch[0]

            optimizer.zero_grad()
            recon = model(x_batch)
            loss = criterion(recon, x_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        epoch_loss = total_loss / num_batches
        scheduler.step(epoch_loss)
        losses.append(epoch_loss)
        current_lr = optimizer.param_groups[0]['lr']
        print(f'Epoch: {epoch + 1}/{epochs} | Loss: {epoch_loss:.6f} | LR: {current_lr:.2e}')

        if save_backup and (epoch + 1) % backup_interval == 0:
            artifacts = BASE_DIR.parent / 'models' / 'artifacts'
            torch.save(model.state_dict(), artifacts / 'ae_model.pt')

            Path.mkdir(artifacts / 'manual_backups' / f'{construction}_construction', exist_ok=True, parents=True)
            shutil.copy(artifacts / 'ae_model.pt',
                        artifacts / 'manual_backups' / f'{construction}_construction' / f'ae_model_{label.replace('*', str(epoch + 1))}.pt')
            shutil.copy(artifacts / 'ae_scaler.pkl',
                        artifacts / 'manual_backups' / f'{construction}_construction' / f'ae_scaler_{label.replace('*', str(epoch + 1))}.pkl')

            print('Manual Backup Saved')
            print(f"Final LR: {optimizer.param_groups[0]['lr']:.2e}")
            print(f'\nFirst epoch loss: {losses[0]:.6f}')
            print(f'Last epoch loss:  {losses[-1]:.6f}')
            print(f'Improvement:      {((losses[0] - losses[-1]) / losses[0]):.1%}')
            losses = []

    if save_backup:
        return None, None

    torch.save(model.state_dict(), BASE_DIR.parent / 'models' / 'artifacts' / 'ae_model.pt')
    return losses[0], losses[-1]

if __name__ == '__main__':
    train_model(
        load=False,
        epochs=250,
        update_scaler=True,
        save_backup=True,
        backup_interval=50,
        label='Initial_*_epochs',
        construction='20_32_16_8'
    )