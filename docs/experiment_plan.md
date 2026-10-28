# Experiment Plan
### NIDS — Machine Learning Evaluation & Validation
## 1. Overview
      
Goal: Evaluate the performance and reliability of the dual-model NIDS pipeline (Random
Forest classifier + Autoencoder anomaly detector) across multiple attack categories and
assess whether combining both models improves detection over either model alone.
## 2. Dataset
### 2.1 Primary Dataset
*Attack Categories are in order of size: greatest -> smallest

| Field                      | Details                                                                                                                                                |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name                       | CIC-IDS-2017                                                                                                                                           |
| Source                     | https://www.unb.ca/cic/datasets/ids-2017.html                                                                                                          |
| Size                       | 3,119,345                                                                                                                                              |
| Class distribution         | 80% Benign - 20% Attack                                                                                                                                |
| Attack categories included | DoS Hulk, PortScan, DDoS, DoS GoldenEye, FTP-Patator, SSH-Patator, DoS slowloris, DoS Slow HTTP Test, Bot, Brute Force, XSS, Sql Injection, Heartbleed |                          |
### 2.2 Preprocessing Steps
- Machine Learning set used for validation
- Generated Labeled flows used for testing and training - 50/50 split
- Column names stripped for consistent formatting
- Keep only the data specified in [Feature Specs](docs/feature_spec.md)
- Features are extracted from the data
- Infinite values are replaced with NaN
- Null values are replaced with zeroes

Autoencoder Only:
- Log1p applied to all features besides absolute difference and byte rate asymmetry
- StandardScaler applied to further normalize the data
- Class weighting applied to model training
### 2.3 Known Limitations of the Dataset
-Attacks such as heartbleed and web-based attacks do not have many flow contributions
-Traffic is overly curated - 'perfect'
-Vulnerable to model drift as it is just one snapshot in time


## 3. Evaluation Metrics
| Metric                            | Applies To    | Why                                                            |
|-----------------------------------|---------------|----------------------------------------------------------------|
| Accuracy                          | Both models   | Baseline, but insufficient alone                               |
| Precision                         | Random Forest | How many flagged flows are actually malicious                  |
| Recall                            | Random Forest | How many actual attacks are caught                             |
| F1 Score                          | Both models   | Balance between precision and recall                           |
| False positive rate               | Both models   | Critical for usability as too many false alarms degrades trust |


## 4. Experiments
### Experiment 1: Random Forest Baseline
**Hypothesis:** A Random Forest trained on flow-level features can classify attack traffic with
high F1 across major attack categories.  
**Setup:**  
- RF is trained on a split CIC-IDS-2017
- Data from CIC-IDS-2017 is imported from the test portion of the split  
- Navigate to [BQ1](../experiments/bq1.py) (which calls the evaluation from [RF-Eval](../evaluation/rf_eval.py)) 
and run the script (the only action needed)

**Features used:** Full list in ***Section 4*** of [Feature Specs](../docs/feature_spec.md)   
**Hyperparameters:**
- n_estimators=300
- max_depth=None
- min_samples_leaf=20
- class_weight='balanced_subsample'
- n_jobs=-1

**Expected outcome:** Model performs extremely well under the same distribution as was trained on  
**Actual results:** See ***Section 5***


### Experiment 2: Autoencoder Anomaly Detection Baseline
**Hypothesis:** An Autoencoder trained only on benign traffic will produce measurably higher
reconstruction error on attack traffic.  
**Setup:**  
- AE is trained on a benign set of a split of CIC-IDS-2017
- Data from CIC-IDS-2017 is imported from the test portion of the split
- Navigate to [BQ1](../experiments/bq1.py) (which calls the evaluation from [AE-Eval](../evaluation/ae_eval.py)) 
and run the script (the only action needed) 

**Architecture:** 20-32-16-8-16-32-20    
**Threshold for anomaly classification:** Calculated on training split of CIC-IDS-2017 via [Thresholds](../util/thresholds.py)   
**Expected outcome:** Model performs well on similar-distribution traffic, 
but may flag too many benign flows (have significant false-positives).   
**Actual results:** See ***Section 5***  
**Notes:** This was done before the data integrity of the pipeline was increased via timeout thresholding & variance calculation being migrated; if re-ran, the performance could increase. 


### Experiment 3: Detection on unseen datasets (UNSW-NB15)
**Hypothesis:** An Autoencoder & Random Forest trained on CIC-IDS-2017 can classify attack traffic on 
unseen datasets such as UNSW-NB15 before undergoing domain adaptation.    
**Setup:**  
- AE and RF are trained on split of CIC-IDS-2017, as experiments 1 & 2; architectures are identical
- UNSW-NB15 dataset is downloaded and dumped in the [UNSW-NB15 Folder](../datasets/UNSW-NB15)
- UNSW-NB15 validation data is imported as implemented in [Experiment-Pathing](../experiments/scripts/paths.py)
- Navigate to [BQ1](../experiments/bq1.py) (which calls the evaluation 
from [AE-Eval](../evaluation/ae_eval.py) and [RF-Eval](../evaluation/rf_eval.py)) and run the script  

**Expected outcome:** Both the models generalize well to differing distributions, but may be a bit lower
than demonstrated in the experiments 1 & 2.  
**Actual results:** See ***Section 5***  
**Notes:** The autoencoder scored lower than expected, and this could be improved via domain adaptation.



## 5. Results Summary
| Experiment               | Precision  | Recall   | F1        | False Positive Rate | Notes                                                                                                                                                                                                                                                        |
|--------------------------|------------|----------|-----------|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| (1) RF Baseline          | 99.9400%   | 99.9133% | 99.9267%  | 0.3529%             | As expected, it performed extremely well on similar-pattern traffic. No issues here.                                                                                                                                                                         |
| (2) Autoencoder Baseline | 90.1280%   | 90.5048% | 90.0579%  | 17.0571%            | It had a higher false-positive rate than expected, but it may potentially be fixed via increased data pipeline integrity.                                                                                                                                    |
| (3) RF on UNSW-NB15      | 95.6352%   | 97.7932% | 96.7022%  | 2.2068%             | As expected, it performed well on this set, though a bit worse than it did on CIC-IDS-2017. It could benefit from the data integrity pipeline changes.                                                                                                       |
| (3) AE on UNSW-NB15      | 82.9429%   | 65.2109% | 73.0158%  | 8.1093%             | It was surprising to see that there was a greater false positive rate on the same dataset it got its training data from; This model could likely benefit from domain adaptation on a set of data with a similar distribution to the set it was evaluated on. |


## 6. Analysis & Conclusions
*Results still unfinished, analysis pending experiment completion*

### 6.1 What Worked  
### 6.2 What Didn’t Work
### 6.3 Limitations of These Experiments  
## 7. Reproducibility Notes
Python version: 3.13.5  

Key library versions:  
- Scikit-learn: 1.8.0  
- Pytorch: 2.10.0  
- Numpy: 2.4.2  
- Pandas: 3.0.1  
- Joblib: 1.5.3  

Random seed(s) used:
- Random Forest State: 42
- Train/Test Split State: 42
- Isolation Forest State: 42
- Auto-encoder Manual Seed: 42  

Hardware/environment:
- Run on CPU (default in this script)
How to run: (reference to a script or notebook)