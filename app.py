from flask import Flask, render_template, request, session
import joblib
import numpy as np
import os

app = Flask(__name__)
app.secret_key = "effort-estimation-secret-key"


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
    # Grooming input
    # -----------------------------
    grooming_input = []
    grooming_has_data = False

    for feature in GROOMING_FEATURES:
        raw = form.get(f"G_{feature}")
        if raw not in (None, "", "0"):
            grooming_has_data = True
        grooming_input.append(safe_float(raw))

    # -----------------------------
    # Implementation input
    # -----------------------------
    implementation_input = []
    implementation_has_data = False

    for feature in IMPLEMENTATION_FEATURES:
        raw = form.get(f"I_{feature}")
        if raw not in (None, "", "0"):
            implementation_has_data = True
        implementation_input.append(safe_float(raw))

    # =================================================
    # ACTION HANDLING WITH MEMORY
    # =================================================
    if action == "grooming":
        if not grooming_has_data:
            error = "Please enter Grooming details."
        else:
            G = np.array(grooming_input).reshape(1, -1)
            grooming_effort = round(float(grooming_model.predict(G)[0]), 2)

            # 🔐 SAVE TO SESSION
            session["grooming_input"] = grooming_input
            session["grooming_effort"] = grooming_effort

    elif action == "implementation":
        if not implementation_has_data:
            error = "Please enter Implementation details."
        else:
            I = np.array(implementation_input).reshape(1, -1)
            implementation_effort = round(
                float(implementation_model.predict(I)[0]), 2
            )

            # 🔐 SAVE TO SESSION
            session["implementation_input"] = implementation_input
            session["implementation_effort"] = implementation_effort

    elif action == "final":
        # Load from session
        grooming_effort = session.get("grooming_effort")
        implementation_effort = session.get("implementation_effort")

        if grooming_effort is None and implementation_effort is None:
            error = "Please calculate Grooming and/or Implementation effort first."
        else:
            if grooming_effort is not None and implementation_effort is not None:
                final_effort = round(grooming_effort + implementation_effort, 2)
            elif grooming_effort is not None:
                final_effort = grooming_effort
            elif implementation_effort is not None:
                final_effort = implementation_effort

    return render_template(
        "index.html",
        grooming_effort=session.get("grooming_effort"),
        implementation_effort=session.get("implementation_effort"),
        final_effort=final_effort,
        error=error
    )

# =================================================
# Run app (Render compatible)
# =================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
