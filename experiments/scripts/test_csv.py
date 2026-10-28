# takes in any .csv file that is labeled and returns the evaluation results based on the ae.eval file to be used on the extracted pcap features
import pandas as pd
from evaluation.ae_eval import evaluate_model as eval_ae
from evaluation.rf_eval import evaluate_model as eval_rf


# <---------- Validation checks ---------->
def path_is_valid(path):
    if path is None:
        print('Received path is invalid: value is None')
        return False
    return True

def eval_type_is_valid(eval_type):
    if eval_type is None:
        print('Eval type is invalid: value is None')
        return False
    if eval_type not in ['ae', 'rf']:
        print('Eval type is invalid: value is not \'ae\' or \'rf\'')
        return False
    return True

def source_type_is_valid(source_type):
    if source_type is None:
        print('Source type is invalid: value is None')
        return False
    return True


def label_is_valid(label):
    if label is None:
        print('Label is invalid: value is None')
        return False
    return True

# <---------- Variable retrieval ---------->
def get_label(validation_features):
    columns_lowercase = {col.lower().strip(): col for col in validation_features.columns}
    return columns_lowercase.get('label') or columns_lowercase.get('labels')


def get_split_features_paths(validation_path, validation_features, label):
    validation_features['_binary_label'] = (validation_features[label] != 'BENIGN') & (validation_features[label] != 0)
    features_benign = validation_features[validation_features['_binary_label'] == False].drop([label,
                                                                                               '_binary_label'], axis=1)
    features_malicious = validation_features[validation_features['_binary_label'] == True].drop([label,
                                                                                                 '_binary_label'], axis=1)

    benign_path = str(validation_path).replace('.csv', '_benign.csv')
    malicious_path = str(validation_path).replace('.csv', '_malicious.csv')

    features_benign.to_csv(benign_path, index=False)
    features_malicious.to_csv(malicious_path, index=False)

    return benign_path, malicious_path


def get_testing_results(eval_type, source_type, validation_path, validation_features, label):
    match eval_type:
        case 'ae':
            benign_validation_path, malicious_validation_path = get_split_features_paths(validation_path, validation_features, label)
            return eval_ae(return_eval=True, features_benign_path=benign_validation_path, features_malicious_path=malicious_validation_path)
        case 'rf':
            return eval_rf(validation_features_path=validation_path, return_eval=True, source_type=source_type)

    return None # will never happen because of eval type check



# <---------- csv test function itself ---------->
def test_csv(validation_path, eval_type, source_type):
    if not eval_type_is_valid(eval_type) or not path_is_valid(validation_path) or not source_type_is_valid(source_type):
        return None

    validation_features = pd.read_csv(validation_path, low_memory=False)
    label_column = get_label(validation_features)

    if not label_is_valid(label_column):
        return None

    return get_testing_results(eval_type, source_type, validation_path, validation_features, label_column)

if __name__ == '__main__':
    test_csv() #input file name