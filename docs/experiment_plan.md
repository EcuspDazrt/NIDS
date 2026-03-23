# Experiment Plan
### NIDS — Machine Learning Evaluation & Validation
## 1. Overview
*Brief description of what this document covers — what you’re testing, why, and what*
*success looks like at a high level.*
      
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
| Metric                            | Applies To    | Why                                                           |
|-----------------------------------|---------------|---------------------------------------------------------------|
| Accuracy                          | Both models   | Baseline, but insufficient alone                              |
| Precision                         | Random Forest | How many flagged flows are actually malicious                 |
| Recall                            | Random Forest | How many actual attacks are caught                            |
| F1 Score                          | Both models   | Balance between precision and recall                          |
| ROC-AUC                           | Both models   | Performance across all thresholds                             |
| Reconstruction error distribution | Autoencoder   | Visualize separation between benign and attack                |
| False positive rate               | Both models   | Critical for usability — too many false alarms degrades trust |
## 4. Experiments
### Experiment 1 — Random Forest Baseline
Hypothesis: A Random Forest trained on flow-level features can classify attack traffic with
high F1 across major attack categories.
Setup:
Training data: (describe)
Features used: (reference feature_spec.md or list here)
Hyperparameters: (n_estimators, max_depth, class_weight, etc.)
What you’re measuring: Per-class precision, recall, F1. Confusion matrix.
Expected outcome: (What do you think will happen and why?)
Actual results: (Fill in after running)
Notes/observations: (Anything unexpected?)
### Experiment 2 — Autoencoder Anomaly Detection Baseline
Hypothesis: An Autoencoder trained only on benign traffic will produce measurably higher
reconstruction error on attack traffic.
Setup:
Training data: benign traffic only
Architecture: (encoder/decoder layer sizes)
Threshold for anomaly classification: (how did you choose this?)
What you’re measuring: Reconstruction error distributions for benign vs. attack, ROC-AUC, false positive rate at chosen threshold.
Expected outcome: (What do you think will happen and why?)
Actual results: (Fill in after running)
Notes/observations:
### Experiment 3 — Layered Detection vs. Single Model
Hypothesis: Combining the Random Forest classification score and the Autoencoder
anomaly score improves overall detection compared to either model alone, particularly on
attack types underrepresented in training data.
Setup:
Risk aggregation method: (weighted average, max, custom logic — describe it)
Comparison baseline: Random Forest alone, Autoencoder alone
What you’re measuring: F1 and false positive rate for all three configurations side by side.
Expected outcome:
Actual results:
Notes/observations:
### Experiment 4 — (Add additional experiments as needed)
Examples worth considering:
How does performance degrade when tested on a different dataset the model wasn’t
trained on?
Which features have the highest importance in the Random Forest? Do any surprise
you?
How does the system perform on novel attack categories it has never seen?
## 5. Results Summary
Fill this in once experiments are complete. A table comparing all experiments side by side.

| Experiment           | Precision | Recall | F1 | ROC-AUC | False Positive Rate | Notes |
|----------------------|-----------|--------|----|---------|---------------------|-------|
| RF Baseline          |           |        |    |         |                     |       |
| Autoencoder Baseline |           |        |    |         |                     |       |
## 6. Analysis & Conclusions
What did the results tell you? What worked, what didn’t, and what would you do differently?
6.1 What Worked
6.2 What Didn’t Work / Surprising Results
6.3 Limitations of These Experiments
6.4 What You’d Test Next
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