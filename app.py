from flask import Flask, render_template, request
import joblib
import numpy as np
import uuid
from datetime import datetime

from csv_manager import append_estimation

app = Flask(__name__)

# =================================================
# Load ML models
# =================================================
grooming_model = joblib.load("grooming_effort_model.pkl")
implementation_model = joblib.load("impl_effort_model.pkl")

GROOMING_FEATURES = list(grooming_model.feature_names_in_)
IMPLEMENTATION_FEATURES = list(implementation_model.feature_names_in_)

MODEL_VERSION = "xgboost-v1"

# =================================================
# Utils
# =================================================
def safe_float(val):
    try:
        if val is None or val == "":
            return 0.0
        return float(val)
    except ValueError:
        return 0.0

# =================================================
# Routes
# =================================================
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    form = request.form
    action = form.get("action")

    # -----------------------------
    # Free-text fields (NOT ML)
    # -----------------------------
    feature_name = form.get("feature_name", "")
    feature_description = form.get("feature_description", "")
    additional_notes = form.get("additional_notes", "")

    # -----------------------------
    # Grooming inputs
    # -----------------------------
    grooming_input = []
    grooming_has_data = False

    for f in GROOMING_FEATURES:
        raw = form.get(f"G_{f}")
        val = safe_float(raw)
        grooming_input.append(val)
        if raw not in (None, "", "0"):
            grooming_has_data = True

    # -----------------------------
    # Implementation inputs
    # -----------------------------
    implementation_input = []
    implementation_has_data = False

    for f in IMPLEMENTATION_FEATURES:
        raw = form.get(f"I_{f}")
        val = safe_float(raw)
        implementation_input.append(val)
        if raw not in (None, "", "0"):
            implementation_has_data = True

    grooming_effort = None
    implementation_effort = None
    final_effort = None

    # -----------------------------
    # Prediction logic
    # -----------------------------
    if action == "grooming":
        if not grooming_has_data:
            return render_template("index.html", error="Please fill Grooming inputs")

        G = np.array(grooming_input).reshape(1, -1)
        grooming_effort = round(float(grooming_model.predict(G)[0]), 2)

    elif action == "implementation":
        if not implementation_has_data:
            return render_template("index.html", error="Please fill Implementation inputs")

        I = np.array(implementation_input).reshape(1, -1)
        implementation_effort = round(float(implementation_model.predict(I)[0]), 2)

    elif action == "final":
        if not grooming_has_data and not implementation_has_data:
            return render_template("index.html", error="Please fill inputs")

        if grooming_has_data:
            G = np.array(grooming_input).reshape(1, -1)
            grooming_effort = round(float(grooming_model.predict(G)[0]), 2)

        if implementation_has_data:
            I = np.array(implementation_input).reshape(1, -1)
            implementation_effort = round(float(implementation_model.predict(I)[0]), 2)

        if grooming_effort is not None and implementation_effort is not None:
            final_effort = round(grooming_effort + implementation_effort, 2)
        elif grooming_effort is not None:
            final_effort = grooming_effort
        elif implementation_effort is not None:
            final_effort = implementation_effort

    # -----------------------------
    # Append to CSV (Checkpoint 4)
    # -----------------------------
    if grooming_effort is not None or implementation_effort is not None:
        estimation_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "estimation_id": estimation_id,

            "feature_name": feature_name,
            "feature_description": feature_description,
            "notes": additional_notes,

            "estimated_by": "default_user",
            "estimation_timestamp": timestamp,

            "model_version": MODEL_VERSION,

            "predicted_grooming_effort": grooming_effort,
            "predicted_implementation_effort": implementation_effort,
            "predicted_final_effort": final_effort,

            "actual_grooming_effort": "",
            "actual_implementation_effort": "",
            "actual_final_effort": "",

            "accuracy_percent": "",
            "error_hours": "",
            "over_under": "",

            "confidence_level": "",
            "validated": ""
        }

        append_estimation(row)

    return render_template(
        "index.html",
        grooming_effort=grooming_effort,
        implementation_effort=implementation_effort,
        final_effort=final_effort
    )

# =================================================
# Run
# =================================================
if __name__ == "__main__":
    app.run(debug=True)
