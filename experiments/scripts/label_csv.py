from datetime import datetime, timezone
from experiments.structs.unswnb_columns import UNSW_COLS

import experiments.scripts.paths as p
import pandas as pd
import socket, ast

JOIN_KEYS = ['Source IP', 'Destination IP', 'Source Port', 'Destination Port']


# <---------- Feature retrieval ---------->
def get_unlabeled_df(unlabeled_path):
    try:
        return pd.read_csv(unlabeled_path)
    except FileNotFoundError:
        print('Unlabeled data not found...')
        return None
    except Exception as e:
        print(f'Error opening unlabeled data: {e}')
        return None


def get_ground_truth_df(gt_path):
    gt = pd.read_csv(gt_path, low_memory=False)
    if gt.empty:
        raise Exception('No ground truth labels found.')
    return gt


# <---------- population and creation funcs ---------->
def populate_ground_truth_dataframes(dfs):
    for i in range(1, 10):  # safe upper bound
        path = p.UNSWNB_DIR / f'UNSW-NB15_{i}.csv'

        if not path.exists():
            print(f'No file {i}, stopping.')
            break

        df = pd.read_csv(path, header=None, names=UNSW_COLS, low_memory=False)
        df['Start time'] = pd.to_numeric(df['Start time'], errors='coerce')
        df = df.dropna(subset=['Start time'])

        if df.empty:
            print(f'File {i} empty after cleaning, skipping.')
            continue

        print(f'File {i}: {datetime.fromtimestamp(df["Start time"].min(), tz=timezone.utc)} -> {datetime.fromtimestamp(df["Start time"].max(), tz=timezone.utc)}')
        dfs.append(df)


def create_full_unswnb_gt():
    print('Creating ground truth file...')

    dfs = []
    populate_ground_truth_dataframes(dfs)

    gt = pd.concat(dfs, ignore_index=True)
    print(f'\nTotal GT flows: {len(gt)} | Attacks: {gt["Label"].sum()}')

    gt.to_csv(p.UNSWNB_GROUND_TRUTH_PATH, index=False)



# <---------- Formatting funcs ----------->
def bytes_str_to_ip(val):
    try:
        b = ast.literal_eval(val)
        return socket.inet_ntoa(b) if len(b) == 4 else socket.inet_ntop(socket.AF_INET6, b)
    except Exception:
        return val


def format_columns(df, df_type):
    match df_type.lower().strip():
        case 'unlabeled':
            for col in ['Source IP', 'Destination IP']:
                df[col] = df[col].apply(bytes_str_to_ip)
            return None
        case 'gt':
            df = df[JOIN_KEYS + ['Attack category'] + ['Label']].copy()
            df['Source Port'] = pd.to_numeric(df['Source Port'], errors='coerce')
            df['Destination Port'] = pd.to_numeric(df['Destination Port'], errors='coerce')
            return df.sort_values('Label', ascending=False).drop_duplicates(subset=JOIN_KEYS, keep='first')
        case _:
            return None



# <---------- Validation checks ----------->
def df_is_labeled(unlabeled_df):
    col_lower = {col.lower().strip(): col for col in unlabeled_df.columns}
    label = col_lower.get('label') or col_lower.get('labels')
    if label is not None:
        print('The csv is already labeled.')
        return True
    return False


def ground_truth_exists(gt_path):
    if gt_path.exists():
        return True
    try:
        create_full_unswnb_gt()
        return True
    except Exception as e:
        print(f'Error creating ground truth file: {e}')
    return False



# <---------- Core functionality ---------->
def label_df(unlabeled_df, gt):
    labeled_df = unlabeled_df.merge(
        gt,
        on=JOIN_KEYS,
        how='left'
    )

    labeled_df['Attack category'] = labeled_df['Attack category'].fillna('Benign')
    labeled_df['Label'] = labeled_df['Label'].fillna(0).astype(int)

    return labeled_df


def save_csv(unlabeled_path, unlabeled_df, labeled_df):
    out_path = str(unlabeled_path).replace('.csv', '_labeled.csv')
    labeled_df.to_csv(out_path, index=False)

    n_attacks = labeled_df['Label'].sum()
    print(f'Done. {n_attacks} attacks, {len(labeled_df) - n_attacks} benign out of {len(unlabeled_df)} total flows.')
    print(f'Written to {out_path}')
    print(labeled_df['Attack category'].value_counts())


def label_csv(unlabeled_path, gt_path):
    unlabeled_df = get_unlabeled_df(unlabeled_path)
    if df_is_labeled(unlabeled_df):
        return
    format_columns(unlabeled_df, 'unlabeled')

    if not ground_truth_exists(gt_path):
        return
    gt = get_ground_truth_df(gt_path)
    gt = format_columns(gt, 'gt')

    labeled_df = label_df(unlabeled_df, gt)

    # ensure the row count did NOT change and dataframe integrity
    assert len(labeled_df) == len(unlabeled_df), f"Row count changed: {len(labeled_df)} != {len(unlabeled_df)}"

    save_csv(unlabeled_path, unlabeled_df, labeled_df)


if __name__ == '__main__':
    label_csv(p.BQ1_CSV_DIR / 'ae_unsw-nb.csv', p.UNSWNB_GROUND_TRUTH_PATH)
