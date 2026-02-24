from flask import Flask, redirect, render_template, request
import joblib
import numpy as np
import pandas as pd
import os
from datetime import datetime
from flask import Flask, redirect, render_template, request, session
app = Flask(__name__)
app.secret_key = "super-secret-key"
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

def clean_note(text):
    import re
    text = str(text)
    text = re.sub(r"[<>]", "", text)   # remove XML breakers
    text = text.replace("&", "and")    # prevent XML corruption
    return text[:1000]                 # limit size

def save_to_sheet(sheet_name, row_dict):

    new_row_df = pd.DataFrame([row_dict])

    if os.path.exists(EXCEL_PATH):

        try:
            existing_df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)

            # ---- Normalize existing columns (for comparison only) ----
            existing_cols_map = {
                col.strip().lower(): col
                for col in existing_df.columns
            }

            # ---- Rename new_row_df columns to match existing ones ----
            for col in new_row_df.columns:
                col_lower = col.strip().lower()
                if col_lower in existing_cols_map:
                    # Rename to exact existing column name
                    new_row_df.rename(
                        columns={col: existing_cols_map[col_lower]},
                        inplace=True
                    )

            # ---- Ensure no duplicate columns ----
            new_row_df = new_row_df.loc[:, ~new_row_df.columns.duplicated()]
            existing_df = existing_df.loc[:, ~existing_df.columns.duplicated()]

            combined_df = pd.concat([new_row_df, existing_df], ignore_index=True)

        except:
            combined_df = new_row_df

        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

    else:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            new_row_df.to_excel(writer, sheet_name=sheet_name, index=False)

# =========HELPER FUNCTION TO CLEAN AND NORMALIZE DATAFRAMES=========
def get_column_name(df, target_name):
    """
    Returns the actual column name in df matching target_name
    irrespective of case or spaces.
    """
    for col in df.columns:
        if col.strip().lower() == target_name.lower():
            return col
    return None

def get_value_case_insensitive(record, target):
    for key in record.keys():
        if key.strip().lower() == target.lower():
            return record[key]
    return ""
# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("home.html")


# ================= GROOMING =================
@app.route("/grooming", methods=["GET", "POST"])
def grooming():

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

        # -------- SAVE GROOMING NOTES --------
        notes_rows = []

        for f in GROOMING_FEATURES:
            field_name = f"G_{f}"
            note_value = request.form.get(f"{field_name}_note", "").strip()

            if note_value:
                notes_rows.append({
                    "Feature_ID": Feature_ID,
                    "Sheet": "Grooming",
                    "Field_Name": field_name,
                    "Note": clean_note(note_value),
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        for note_row in notes_rows:
            save_to_sheet("Notes", note_row)

        session["modal_result"] = effort
        return redirect("/grooming")

    effort = session.pop("modal_result", None)
    return render_template("grooming.html", effort=effort)

# ================= IMPLEMENTATION =================
@app.route("/implementation", methods=["GET", "POST"])
def implementation():

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

        # -------- SAVE IMPLEMENTATION NOTES --------
        notes_rows = []

        for f in IMPLEMENTATION_FEATURES:
            field_name = f"I_{f}"
            note_value = request.form.get(f"{field_name}_note", "").strip()

            if note_value:
                notes_rows.append({
                    "Feature_ID": Feature_ID,
                    "Sheet": "Implementation",
                    "Field_Name": field_name,
                    "Note": clean_note(note_value),
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        for note_row in notes_rows:
            save_to_sheet("Notes", note_row)

        session["modal_result"] = effort
        return redirect("/implementation")

    modal_result = session.pop("modal_result", None)
    return render_template("implementation.html", effort=modal_result)

# ================= FINAL =================
@app.route("/final", methods=["GET", "POST"])
def final():

    action = None
    grooming_record = None
    implementation_record = None
    final_effort = None
    feature_id = ""
    query = request.args.get("feature_id", "")  # ✅ KEEP THIS

    if request.method == "POST":

        query = request.form.get("feature_id", "").strip()
        action = request.form.get("action")

        if query and os.path.exists(EXCEL_PATH):
            with pd.ExcelFile(EXCEL_PATH) as xls:

                # ---------- GROOMING ----------
                if "Grooming" in xls.sheet_names:
                    g_df = pd.read_excel(EXCEL_PATH, sheet_name="Grooming")
                    if not g_df.empty:

                        g_df = g_df.loc[:, ~g_df.columns.duplicated()]
                        g_df = g_df.fillna("")

                        fid_col = get_column_name(g_df, "feature_id")
                        fname_col = get_column_name(g_df, "feature_name")

                        if fid_col:
                            g_df[fid_col] = g_df[fid_col].apply(lambda x: str(x).strip())
                        if fname_col:
                            g_df[fname_col] = g_df[fname_col].apply(lambda x: str(x).strip())

                        if fid_col and fname_col:
                            match = g_df[
                                (g_df[fid_col] == query) |
                                (g_df[fname_col].str.lower() == query.lower())
                            ]

                            if not match.empty:
                                grooming_record = match.iloc[0].to_dict()
                                feature_id = grooming_record.get(fid_col, "")

                # ---------- IMPLEMENTATION ----------
                if "Implementation" in xls.sheet_names:
                    i_df = pd.read_excel(EXCEL_PATH, sheet_name="Implementation")
                    if not i_df.empty:

                        i_df = i_df.loc[:, ~i_df.columns.duplicated()]
                        i_df = i_df.fillna("")

                        fid_col = get_column_name(i_df, "feature_id")
                        fname_col = get_column_name(i_df, "feature_name")

                        if fid_col:
                            i_df[fid_col] = i_df[fid_col].apply(lambda x: str(x).strip())
                        if fname_col:
                            i_df[fname_col] = i_df[fname_col].apply(lambda x: str(x).strip())

                        if fid_col and fname_col:
                            match = i_df[
                                (i_df[fid_col] == feature_id) |
                                (i_df[fname_col].str.lower() == query.lower())
                            ]

                            if not match.empty:
                                implementation_record = match.iloc[0].to_dict()

        # ---------- CALCULATE ----------
        if action == "calculate" and grooming_record and implementation_record:

            g_effort = safe(grooming_record.get("grooming_effort"))
            i_effort = safe(implementation_record.get("implementation_effort"))
            final_effort = round(g_effort + i_effort, 2)

            row = {
                "feature_id": feature_id,
                "feature_name": get_value_case_insensitive(grooming_record, "feature_name"),
                "grooming_effort": g_effort,
                "implementation_effort": i_effort,
                "final_effort": final_effort,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            save_to_sheet("Final", row)

            session["modal_result"] = final_effort
            return redirect(f"/final?feature_id={query}")

    # ✅ ONLY POP HERE
    modal_result = session.pop("modal_result", None)

    return render_template(
        "final.html",
        grooming=grooming_record,
        implementation=implementation_record,
        final_effort=modal_result,
        feature_id=query,
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

        # ✅ Load Notes sheet ONCE
        notes_df = None
        if "Notes" in xls.sheet_names:
            notes_df = pd.read_excel(EXCEL_PATH, sheet_name="Notes")
            notes_df = notes_df.fillna("")
            # Normalize column names
            notes_df.columns = notes_df.columns.astype(str).str.strip()

            # Find actual column names safely
            feature_id_col_notes = None
            sheet_col_notes = None
            field_col_notes = None
            note_col_notes = None

            for col in notes_df.columns:
                if col.strip().lower() == "feature_id":
                    feature_id_col_notes = col
                elif col.strip().lower() == "sheet":
                    sheet_col_notes = col
                elif col.strip().lower() == "field_name":
                    field_col_notes = col
                elif col.strip().lower() == "note":
                    note_col_notes = col

            # If required columns missing → skip notes safely
            if not feature_id_col_notes or not sheet_col_notes:
                notes_df = None
            else:
                notes_df[feature_id_col_notes] = notes_df[feature_id_col_notes].astype(str).str.strip()
                notes_df[sheet_col_notes] = notes_df[sheet_col_notes].astype(str).str.strip()
        for sheet in xls.sheet_names:

            # ❌ Skip Notes sheet itself
            if sheet.strip().lower() == "notes":
                continue

            df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

            if df.empty:
                continue

            df.columns = df.columns.astype(str).str.strip()
            df = df.loc[:, ~df.columns.duplicated()]
            df = df.fillna("")

            feature_id_col = None
            feature_name_col = None

            for col in df.columns:
                if col.strip().lower() == "feature_id":
                    feature_id_col = col
                if col.strip().lower() == "feature_name":
                    feature_name_col = col

            if not feature_id_col:
                continue

            df[feature_id_col] = df[feature_id_col].astype(str).str.strip()

            if feature_name_col:
                df[feature_name_col] = df[feature_name_col].astype(str).str.strip()
            else:
                df["feature_name"] = ""
                feature_name_col = "feature_name"

            query_clean = str(query).strip()

            filtered = df[
                (df[feature_id_col] == query_clean) |
                (df[feature_name_col].str.lower() == query_clean.lower())
            ]

            if filtered.empty:
                continue

            records = filtered.to_dict(orient="records")

            # ✅ Attach notes properly
            if notes_df is not None:
                for record in records:

                    fid = str(record.get(feature_id_col, "")).strip()
                    sheet_name_clean = sheet.strip()

                    field_notes = notes_df[
                        (notes_df[feature_id_col_notes] == fid) &
                        (notes_df[sheet_col_notes] == sheet_name_clean)
                    ]

                    for _, note_row in field_notes.iterrows():
                        field = note_row[field_col_notes]
                        note = note_row[note_col_notes]

                        record[f"{field}_NOTE"] = note

            # Clean empty values
            for record in records:
                for k, v in record.items():
                    if v == "" or str(v).lower() == "nan":
                        record[k] = "---"

            sheet_name = sheet.strip().lower()

            if sheet_name == "grooming":
                grooming_results = records
            elif sheet_name == "implementation":
                implementation_results = records
            elif sheet_name == "final":
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

    next_page = request.args.get("next", "search")  # 👈 capture source

    if not os.path.exists(EXCEL_PATH):
        return "Excel file not found"

    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

    if df.empty:
        return "Sheet is empty"

    df.columns = df.columns.str.strip()

    # Find feature_id column irrespective of case
    feature_id_col = None
    for col in df.columns:
        if col.strip().lower() == "feature_id":
            feature_id_col = col
            break

    if not feature_id_col:
        return "feature_id column missing"

    df[feature_id_col] = df[feature_id_col].fillna("").astype(str).str.strip()
    feature_id = str(feature_id).strip()

    record = df[df[feature_id_col] == feature_id]

    if record.empty:
        return "Record not found"

    if request.method == "POST":

        for col in df.columns:
            if col in request.form:
                df.loc[df[feature_id_col] == feature_id, col] = request.form[col]

        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)

        # 👇 Redirect back properly
        if next_page == "final":
            return redirect("/final")
        else:
            return redirect("/search")

    row_data = record.iloc[0].fillna("---").to_dict()

    return render_template("edit.html", row=row_data, sheet=sheet)

if __name__ == "__main__":
    app.run(debug=True)