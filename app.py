from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)

# =================================================
# Load trained models
# =================================================
grooming_model = joblib.load("grooming_effort_model.pkl")
implementation_model = joblib.load("impl_effort_model.pkl")

# Feature order MUST match training
GROOMING_FEATURES = list(grooming_model.feature_names_in_)
IMPLEMENTATION_FEATURES = list(implementation_model.feature_names_in_)

# =================================================
# Utility: Safe float conversion
# =================================================
def safe_float(value):
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except ValueError:
        return 0.0

# =================================================
# Home route
# =================================================
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# =================================================
# Predict route (MAIN LOGIC)
# =================================================
@app.route("/predict", methods=["POST"])
def predict():
    form = request.form

    # -----------------------------
    # Grooming inputs
    # -----------------------------
    grooming_input = []
    grooming_has_data = False

    for feature in GROOMING_FEATURES:
        raw_value = form.get(f"G_{feature}")
        value = safe_float(raw_value)
        grooming_input.append(value)

        # Detect at least one meaningful input
        if raw_value not in (None, "", "0"):
            grooming_has_data = True

    # -----------------------------
    # Implementation inputs
    # -----------------------------
    implementation_input = []
    implementation_has_data = False

    for feature in IMPLEMENTATION_FEATURES:
        raw_value = form.get(f"I_{feature}")
        value = safe_float(raw_value)
        implementation_input.append(value)

        # Detect at least one meaningful input
        if raw_value not in (None, "", "0"):
            implementation_has_data = True

    # -----------------------------
    # 🚨 Validation: block empty submit
    # -----------------------------
    if not grooming_has_data and not implementation_has_data:
        return render_template(
            "index.html",
            error="Please enter Grooming and/or Implementation details before calculating effort."
        )

    # -----------------------------
    # Predict Grooming Effort
    # -----------------------------
    G = np.array(grooming_input).reshape(1, -1)
    grooming_effort = float(grooming_model.predict(G)[0])
    grooming_effort = round(grooming_effort, 2)

    # -----------------------------
    # Predict Implementation Effort
    # -----------------------------
    I = np.array(implementation_input).reshape(1, -1)
    implementation_effort = float(implementation_model.predict(I)[0])
    implementation_effort = round(implementation_effort, 2)

    # -----------------------------
    # Final Effort
    # -----------------------------
    final_effort = round(grooming_effort + implementation_effort, 2)

    return render_template(
        "index.html",
        grooming_effort=grooming_effort,
        implementation_effort=implementation_effort,
        final_effort=final_effort
    )

# =================================================
# Run app
# =================================================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
