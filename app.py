from flask import Flask, render_template, request
import joblib
import numpy as np
import os

app = Flask(__name__)

# =================================================
# Load trained XGBoost models
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
# Predict route (PHASE-AWARE LOGIC)
# =================================================
@app.route("/predict", methods=["POST"])
def predict():
    form = request.form
    action = form.get("action")

    grooming_effort = None
    implementation_effort = None
    final_effort = None
    error = None

    # -----------------------------
    # Prepare Grooming input
    # -----------------------------
    grooming_input = []
    grooming_has_data = False

    for feature in GROOMING_FEATURES:
        raw = form.get(f"G_{feature}")
        if raw not in (None, "", "0"):
            grooming_has_data = True
        grooming_input.append(safe_float(raw))

    # -----------------------------
    # Prepare Implementation input
    # -----------------------------
    implementation_input = []
    implementation_has_data = False

    for feature in IMPLEMENTATION_FEATURES:
        raw = form.get(f"I_{feature}")
        if raw not in (None, "", "0"):
            implementation_has_data = True
        implementation_input.append(safe_float(raw))

    # =================================================
    # ACTION HANDLING
    # =================================================
    if action == "grooming":
        if not grooming_has_data:
            error = "Please enter Grooming details."
        else:
            G = np.array(grooming_input).reshape(1, -1)
            grooming_effort = round(
                float(grooming_model.predict(G)[0]), 2
            )

    elif action == "implementation":
        if not implementation_has_data:
            error = "Please enter Implementation details."
        else:
            I = np.array(implementation_input).reshape(1, -1)
            implementation_effort = round(
                float(implementation_model.predict(I)[0]), 2
            )

    elif action == "final":
        if not grooming_has_data and not implementation_has_data:
            error = "Please enter Grooming and/or Implementation details."
        else:
            if grooming_has_data:
                G = np.array(grooming_input).reshape(1, -1)
                grooming_effort = round(
                    float(grooming_model.predict(G)[0]), 2
                )

            if implementation_has_data:
                I = np.array(implementation_input).reshape(1, -1)
                implementation_effort = round(
                    float(implementation_model.predict(I)[0]), 2
                )

            if grooming_effort is not None and implementation_effort is not None:
                final_effort = round(grooming_effort + implementation_effort, 2)
            elif grooming_effort is not None:
                final_effort = grooming_effort
            elif implementation_effort is not None:
                final_effort = implementation_effort

    # =================================================
    # Render response
    # =================================================
    return render_template(
        "index.html",
        grooming_effort=grooming_effort,
        implementation_effort=implementation_effort,
        final_effort=final_effort,
        error=error
    )

# =================================================
# Run app (Render compatible)
# =================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
