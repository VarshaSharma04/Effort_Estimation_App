from flask import Flask, render_template, request
import joblib
import numpy as np
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_PATH = "Effort_Estimation_Grooming_Implementation_FINAL.xlsx"

# ================= LOAD MODELS =================
grooming_model = joblib.load("grooming_effort_model.pkl")
implementation_model = joblib.load("impl_effort_model.pkl")

GROOMING_FEATURES = list(grooming_model.feature_names_in_)
IMPLEMENTATION_FEATURES = list(implementation_model.feature_names_in_)

# ================= UTILITIES =================
def safe(value):
    try:
        return float(value)
    except:
        return 0.0


def save_entry(entry):
    df_new = pd.DataFrame([entry])

    if os.path.exists(EXCEL_PATH):
        df_old = pd.read_excel(EXCEL_PATH)

        # Make schema consistent
        for col in df_old.columns:
            if col not in df_new.columns:
                df_new[col] = ""

        for col in df_new.columns:
            if col not in df_old.columns:
                df_old[col] = ""

        df = pd.concat([df_new, df_old], ignore_index=True)
    else:
        df = df_new

    df.to_excel(EXCEL_PATH, index=False)


def get_last_entry(entry_type):
    if not os.path.exists(EXCEL_PATH):
        return None

    df = pd.read_excel(EXCEL_PATH)

    if df.empty or "type" not in df.columns:
        return None

    filtered = df[df["type"] == entry_type]

    if filtered.empty:
        return None

    return filtered.iloc[0].to_dict()


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- GROOMING ----------------
@app.route("/grooming", methods=["GET", "POST"])
def grooming():
    effort = None

    if request.method == "POST":
        values = [safe(request.form.get(f"G_{f}", 0)) for f in GROOMING_FEATURES]

        effort = round(
            float(grooming_model.predict(np.array(values).reshape(1, -1))[0]),
            2
        )

        entry = {
            "type": "grooming",
            "effort": effort,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save full grooming inputs
        for f in GROOMING_FEATURES:
            entry[f"G_{f}"] = request.form.get(f"G_{f}", 0)

        save_entry(entry)

    return render_template("grooming.html", effort=effort)


# ---------------- IMPLEMENTATION ----------------
@app.route("/implementation", methods=["GET", "POST"])
def implementation():
    effort = None

    if request.method == "POST":
        values = [safe(request.form.get(f"I_{f}", 0)) for f in IMPLEMENTATION_FEATURES]

        effort = round(
            float(implementation_model.predict(np.array(values).reshape(1, -1))[0]),
            2
        )

        entry = {
            "type": "implementation",
            "effort": effort,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save full implementation inputs
        for f in IMPLEMENTATION_FEATURES:
            entry[f"I_{f}"] = request.form.get(f"I_{f}", 0)

        save_entry(entry)

    return render_template("implementation.html", effort=effort)


# ---------------- FINAL REVIEW ----------------
@app.route("/final", methods=["GET", "POST"])
def final():
    last_grooming = get_last_entry("grooming")
    last_implementation = get_last_entry("implementation")

    final_effort = None

    if request.method == "POST":
        if last_grooming and last_implementation:
            g = float(last_grooming.get("effort", 0))
            i = float(last_implementation.get("effort", 0))

            final_effort = round(g + i, 2)

            save_entry({
                "type": "final",
                "grooming_effort": g,
                "implementation_effort": i,
                "final_effort": final_effort,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return render_template(
        "final.html",
        grooming=last_grooming,
        implementation=last_implementation,
        final_effort=final_effort
    )


# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if not os.path.exists(EXCEL_PATH):
        data = []
    else:
        data = pd.read_excel(EXCEL_PATH).to_dict(orient="records")

    return render_template("history.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)
