from flask import Flask, redirect, render_template, request
import joblib
import numpy as np
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_PATH = "Effort_Estimation_Grooming_Implementation_FINAL.xlsx"

# Load models
grooming_model = joblib.load("grooming_effort_model.pkl")
implementation_model = joblib.load("impl_effort_model.pkl")

GROOMING_FEATURES = list(grooming_model.feature_names_in_)
IMPLEMENTATION_FEATURES = list(implementation_model.feature_names_in_)


# ================= UTIL =================
def safe(v):
    try:
        return float(v)
    except:
        return 0.0


def save_to_sheet(sheet_name, row_dict):
    new_row_df = pd.DataFrame([row_dict])

    if os.path.exists(EXCEL_PATH):

        try:
            existing_df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
            combined_df = pd.concat([new_row_df, existing_df], ignore_index=True)
        except:
            combined_df = new_row_df

        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

    else:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            new_row_df.to_excel(writer, sheet_name=sheet_name, index=False)


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("home.html")


# ================= GROOMING =================
@app.route("/grooming", methods=["GET", "POST"])
def grooming():
    effort = None

    if request.method == "POST":

        Feature_ID = request.form.get("Feature_ID", "").strip()
        Feature_Name = request.form.get("Feature_Name", "").strip()


        values = []
        input_data = {}

        for f in GROOMING_FEATURES:
            val = safe(request.form.get(f"G_{f}", 0))
            values.append(val)
            input_data[f] = val

        effort = round(float(
            grooming_model.predict(np.array(values).reshape(1, -1))[0]
        ), 2)

        row = {
            "Feature_ID": Feature_ID,
            "Feature_Name": Feature_Name,
            "grooming_effort": effort,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        row.update(input_data)

        save_to_sheet("Grooming", row)

    return render_template("grooming.html", effort=effort)


# ================= IMPLEMENTATION =================
@app.route("/implementation", methods=["GET", "POST"])
def implementation():
    effort = None

    if request.method == "POST":

        Feature_ID = request.form.get("Feature_ID", "").strip()
        Feature_Name = request.form.get("Feature_Name", "").strip()

        values = []
        input_data = {}

        for f in IMPLEMENTATION_FEATURES:
            val = safe(request.form.get(f"I_{f}", 0))
            values.append(val)
            input_data[f] = val

        effort = round(float(
            implementation_model.predict(np.array(values).reshape(1, -1))[0]
        ), 2)

        row = {
            "Feature_ID": Feature_ID,
            "Feature_Name": Feature_Name,
            "implementation_effort": effort,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        row.update(input_data)

        save_to_sheet("Implementation", row)

    return render_template("implementation.html", effort=effort)


# ================= FINAL =================
@app.route("/final", methods=["GET", "POST"])
def final():

    grooming_record = None
    implementation_record = None
    final_effort = None
    feature_id = ""
    query = ""

    if request.method == "POST":

        query = request.form.get("feature_id", "").strip()
        action = request.form.get("action")

        if query and os.path.exists(EXCEL_PATH):

            with pd.ExcelFile(EXCEL_PATH) as xls:

                # ---------- GROOMING ----------
                if "Grooming" in xls.sheet_names:
                    g_df = pd.read_excel(EXCEL_PATH, sheet_name="Grooming")
                    g_df.columns = g_df.columns.str.strip().str.lower()
                    g_df = g_df.fillna("")

                    g_df["feature_id"] = g_df["feature_id"].astype(str).str.strip()
                    g_df["feature_name"] = g_df["feature_name"].astype(str).str.strip()

                    match = g_df[
                        (g_df["feature_id"] == query) |
                        (g_df["feature_name"].str.lower() == query.lower())
                    ]

                    if not match.empty:
                        grooming_record = match.iloc[0].to_dict()
                        feature_id = grooming_record.get("feature_id", "")

                # ---------- IMPLEMENTATION ----------
                if "Implementation" in xls.sheet_names:
                    i_df = pd.read_excel(EXCEL_PATH, sheet_name="Implementation")
                    i_df.columns = i_df.columns.str.strip().str.lower()
                    i_df = i_df.fillna("")

                    i_df["feature_id"] = i_df["feature_id"].astype(str).str.strip()
                    i_df["feature_name"] = i_df["feature_name"].astype(str).str.strip()

                    match = i_df[
                        (i_df["feature_id"] == feature_id) |
                        (i_df["feature_name"].str.lower() == query.lower())
                    ]

                    if not match.empty:
                        implementation_record = match.iloc[0].to_dict()

        # ---------- CALCULATE ----------
        if action == "calculate" and grooming_record and implementation_record:

            g_effort = float(grooming_record.get("grooming_effort", 0))
            i_effort = float(implementation_record.get("implementation_effort", 0))

            final_effort = round(g_effort + i_effort, 2)

            row = {
                "feature_id": grooming_record.get("feature_id", ""),
                "feature_name": grooming_record.get("feature_name", ""),
                "grooming_effort": g_effort,
                "implementation_effort": i_effort,
                "final_effort": final_effort,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            save_to_sheet("Final", row)

    return render_template(
        "final.html",
        grooming=grooming_record,
        implementation=implementation_record,
        final_effort=final_effort,
        feature_id=query
    )


# ================= HISTORY HOME =================
@app.route("/history")
def history_home():
    return render_template("history_home.html")


# ================= GROOMING HISTORY =================
@app.route("/history/grooming")
def grooming_history():

    if not os.path.exists(EXCEL_PATH):
        return render_template("history_table.html", title="Grooming History", rows=[])

    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="Grooming")
        rows = df.to_dict(orient="records")
    except:
        rows = []

    return render_template("history_table.html", title="Grooming History", rows=rows)


# ================= IMPLEMENTATION HISTORY =================
@app.route("/history/implementation")
def implementation_history():

    if not os.path.exists(EXCEL_PATH):
        return render_template("history_table.html", title="Implementation History", rows=[])

    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="Implementation")
        rows = df.to_dict(orient="records")
    except:
        rows = []

    return render_template("history_table.html", title="Implementation History", rows=rows)


# ================= FINAL HISTORY =================
@app.route("/history/final")
def final_history():

    if not os.path.exists(EXCEL_PATH):
        return render_template("history_table.html", title="Final History", rows=[])

    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="Final")
        rows = df.to_dict(orient="records")
    except:
        rows = []

    return render_template("history_table.html", title="Final History", rows=rows)



# ================= SEARCH =================
@app.route("/search", methods=["GET", "POST"])
def search():

    grooming_results = []
    implementation_results = []
    final_results = []

    if request.method == "POST":

        query = request.form.get("query", "").strip()

        if query == "" or not os.path.exists(EXCEL_PATH):
            return render_template(
                "search.html",
                grooming_results=[],
                implementation_results=[],
                final_results=[]
            )

        xls = pd.ExcelFile(EXCEL_PATH)

        for sheet in xls.sheet_names:

            df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

            if df.empty:
                continue

            # Normalize columns safely
            df.columns = df.columns.astype(str).str.strip().str.lower()

            # Remove duplicate columns completely
            df = df.loc[:, ~df.columns.duplicated()]

            df = df.fillna("")

            # Ensure required columns exist
            if "feature_id" not in df.columns:
                continue

            # Convert safely WITHOUT using .str on column selection
            df["feature_id"] = df["feature_id"].apply(lambda x: str(x).strip())

            if "feature_name" in df.columns:
                df["feature_name"] = df["feature_name"].apply(lambda x: str(x).strip())
            else:
                df["feature_name"] = ""

            # Exact match only
            filtered = df[
                (df["feature_id"] == query) |
                (df["feature_name"].str.lower() == query.lower())
            ]

            if filtered.empty:
                continue

            records = filtered.to_dict(orient="records")

            # Replace empty with ---
            for record in records:
                for k, v in record.items():
                    if v == "" or str(v).lower() == "nan":
                        record[k] = "---"

            if sheet.lower() == "grooming":
                grooming_results = records

            elif sheet.lower() == "implementation":
                implementation_results = records

            elif sheet.lower() == "final":
                final_results = records

    return render_template(
        "search.html",
        grooming_results=grooming_results,
        implementation_results=implementation_results,
        final_results=final_results
    )

# ================= EDIT =================
@app.route("/edit/<sheet>/<feature_id>", methods=["GET", "POST"])
def edit(sheet, feature_id):

    if not os.path.exists(EXCEL_PATH):
        return "Excel file not found"

    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

    if df.empty:
        return "Sheet is empty"

    # Normalize column names
    df.columns = df.columns.str.strip()

    if "feature_id" not in df.columns:
        return "feature_id column missing"

    df["feature_id"] = df["feature_id"].fillna("").astype(str).str.strip()

    feature_id = str(feature_id).strip()

    record = df[df["feature_id"] == feature_id]

    if record.empty:
        return "Record not found"

    if request.method == "POST":

        for col in df.columns:
            if col in request.form:
                df.loc[df["feature_id"] == feature_id, col] = request.form[col]

        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)

        return redirect("/search")

    row_data = record.iloc[0].fillna("---").to_dict()

    return render_template("edit.html", row=row_data, sheet=sheet)

if __name__ == "__main__":
    app.run(debug=True)
