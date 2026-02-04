# train.py (with adversarial training and data augmentation)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import pickle
from features import extract_features

# Stub for data generation (replace with real dataset loading)
def generate_sample_data(num_samples=100):
    # Synthetic: AI = clean, Human = chaotic
    ai_codes = [f"def func(x):\n    return x * 2" for _ in range(num_samples // 2)]
    human_codes = [f"def funky_var(y):  # TODO: optimize\n    print('debug')\n    return y * 2" for _ in range(num_samples // 2)]
    df = pd.DataFrame({"code": ai_codes + human_codes, "label": [0] * (num_samples // 2) + [1] * (num_samples // 2)})
    return df

# Adversarial generator: game AI code to mimic human
def generate_adversarial(ai_code: str):
    # Add fake comments, TODOs, quirky vars
    lines = ai_code.splitlines()
    lines.insert(1, "# Fake TODO: something")
    lines = [re.sub(r'\b(x)\b', 'quirky_x', line) for line in lines]
    return '\n'.join(lines + ["print('fake debug')"])  # Label as 0 (AI/gamed)

df = generate_sample_data(200)  # Or load real: pd.read_csv('data.csv')

# Augment with adversarial (10% of data)
adv_samples = []
for code, label in zip(df[df['label'] == 0]['code'], df[df['label'] == 0]['label']):
    adv_code = generate_adversarial(code)
    adv_samples.append({"code": adv_code, "label": 0})  # Still AI
df_adv = pd.DataFrame(adv_samples)
df = pd.concat([df, df_adv], ignore_index=True)

# Extract features
features_list = [extract_features(code) for code in df["code"]]
df_features = pd.DataFrame(features_list)
df_features["label"] = df["label"]

X = df_features.drop("label", axis=1)
y = df_features["label"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = XGBClassifier(n_estimators=200, max_depth=6)
model.fit(X_train, y_train)

# Save
with open("soul_model_v1.pkl", "wb") as f:  # Removed 'models/' for flat
    pickle.dump(model, f)

print("Accuracy:", model.score(X_test, y_test))