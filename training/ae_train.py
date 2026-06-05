import numpy as np
import util.paths as p
import torch.nn as nn
import torch.optim as optim
import torch, shutil, random

from util.feature_retrieval import get_ae_features_training
from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model
from tqdm import tqdm

from util.logger import get_logger

LOGGER = get_logger(__name__)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def copy_ae_into_construction(construction, label, epoch):
    shutil.copy(p.AE_WEIGHTS_PATH, p.MANUAL_BACKUPS_DIR / f'{construction}_construction' / f'ae_model_{label.replace('*', str(epoch + 1))}.pt')
    shutil.copy(p.AE_SCALER_PATH, p.MANUAL_BACKUPS_DIR / f'{construction}_construction' / f'ae_scaler_{label.replace('*', str(epoch + 1))}.pkl')


def save_interval(model, construction, label, epoch, optimizer, losses):
    torch.save(model.state_dict(), p.AE_WEIGHTS_PATH)
    copy_ae_into_construction(construction, label, epoch)

    LOGGER.info('Manual Backup Saved')
    LOGGER.info(f"Final LR: {optimizer.param_groups[0]['lr']:.2e}")
    LOGGER.info(f'\nFirst epoch loss: {losses[0]:.6f}')
    LOGGER.info(f'Last epoch loss:  {losses[-1]:.6f}')
    LOGGER.info(f'Improvement:      {((losses[0] - losses[-1]) / losses[0]):.1%}')


def prep_training(load):
    model = construct_model(load=load)
    criterion = nn.MSELoss(reduction='mean')
    optimizer = optim.Adam(model.parameters(), lr=3e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-6)

    return model, criterion, optimizer, scheduler


def run_epoch(model, optimizer, criterion, scheduler, losses, epoch, epochs, training_features):
    model.train()
    total_loss = 0.0
    num_batches = 0
    for batch in training_features:
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
    tqdm.write(f'Epoch: {epoch + 1}/{epochs} | Loss: {epoch_loss:.6f} | LR: {current_lr:.2e}')


def train_model(load=False, epochs=20, features=None, batch_size=2048, update_scaler=False, save_backup=False, backup_interval=None, label='', construction=''):
    LOGGER.info('Autoencoder began training')
    if not p.processed_dataset_exists():
        return None, None
    if features is None:
        features = get_ae_features_training()

    x_train = create_dataset(features, batch_size, update_scaler=update_scaler)
    model, criterion, optimizer, scheduler = prep_training(load=load)
    losses = []

    # training loop
    for epoch in tqdm(range(epochs), total=epochs, desc='ae training'):
        run_epoch(model, optimizer, criterion, scheduler, losses, epoch, epochs, x_train)
        if save_backup and (epoch + 1) % backup_interval == 0:
            save_interval(model, construction, label, epoch, optimizer, losses)
            losses = []

    torch.save(model.state_dict(), p.AE_WEIGHTS_PATH)

    LOGGER.info('Autoencoder finished training')
    if save_backup:
        return None, None
    return losses[0], losses[-1]



# <---------- Training presets ---------->
def train_model_with_backup_interval():
    train_model(
        load=False,
        epochs=250,
        update_scaler=True,
        save_backup=True,
        backup_interval=50,
        label='Initial_*_epochs',
        construction='20_32_16_8'
    )

def train_most_optimized_model():
    train_model(
        load=False,
        epochs=150,
        update_scaler=True,
        save_backup=False,
    )


if __name__ == '__main__':
    train_most_optimized_model()
