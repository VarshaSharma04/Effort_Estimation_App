import joblib
import pandas as pd

# -----------------------------
# Load trained model
# -----------------------------
model = joblib.load("grooming_effort_model.pkl")

# -----------------------------
# Get feature names FROM MODEL
# (this includes trailing spaces)
# -----------------------------
MODEL_FEATURES = model.get_booster().feature_names

# -----------------------------
# Read input file (clean keys)
# -----------------------------
raw_input = {}

with open("grooming_input.txt", "r") as file:
    for line in file:
        key, value = line.strip().split("=")
        raw_input[key.strip()] = float(value.strip())

# -----------------------------
# Map clean keys to model keys
# -----------------------------
mapped_input = {}

for model_feature in MODEL_FEATURES:
    clean_feature = model_feature.strip()

    if clean_feature not in raw_input:
        raise ValueError(f"Missing feature in input file: {clean_feature}")

    mapped_input[model_feature] = raw_input[clean_feature]

# -----------------------------
# Create DataFrame (schema-safe)
# -----------------------------
input_df = pd.DataFrame([[mapped_input[f] for f in MODEL_FEATURES]],
                        columns=MODEL_FEATURES)

# -----------------------------
# Predict effort
# -----------------------------
predicted_effort = model.predict(input_df)[0]

# -----------------------------
# Output
# -----------------------------
print("\n===================================")
print(f"Estimated Grooming Effort (Hours): {predicted_effort:.2f}")
print("===================================\n")
