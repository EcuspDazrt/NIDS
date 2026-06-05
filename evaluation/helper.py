import json
from sklearn.metrics import classification_report

# <---------- Formatting evaluation output and printing it ---------->
def print_indented(eval_dict):
    print(json.dumps(eval_dict, indent=2))


def print_report(labels, predictions):
    print(classification_report(labels, predictions))