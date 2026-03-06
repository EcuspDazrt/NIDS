import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

from scripts.build_dataset import create_dataset
from models.definitions.autoencoder import construct_model

from pathlib import Path
BASE_DIR = Path(__file__).parent

def train_model():
    # initialize training variables
    batch_size = 2048
    epochs = 100

    # create dataset
    features = pd.read_csv(BASE_DIR.parent/'datasets'/'processed'/'ae_training.csv', low_memory=False)
    x_train = create_dataset(features, batch_size, training=True)

    # construct model
    model = construct_model()
    criterion = nn.MSELoss(reduction='mean')
    optimizer = optim.Adam(model.parameters(), lr=1e-5)

    for epoch in range(epochs):
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

        print(f'Epochs: {epoch + 1} / {epochs}, Loss: {total_loss / num_batches}')
        torch.save(model.state_dict(), BASE_DIR.parent/'models'/'artifacts'/'ae_model.pt')

train_model()