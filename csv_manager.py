import csv
import os
from datetime import datetime

CSV_PATH = os.path.join("data", "effort_estimations.csv")

CSV_HEADERS = [
    "estimation_id",
    "feature_name",
    "feature_description",
    "notes",
    "estimated_by",
    "estimation_timestamp",
    "model_version",
    "predicted_grooming_effort",
    "predicted_implementation_effort",
    "predicted_final_effort",
    "actual_grooming_effort",
    "actual_implementation_effort",
    "actual_final_effort",
    "accuracy_percent",
    "error_hours",
    "over_under",
    "confidence_level",
    "validated"
]


def ensure_csv_exists():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()


def append_estimation(row: dict):
    """
    Call this at prediction time
    """
    ensure_csv_exists()

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row)


def list_estimation_ids():
    """
    DEBUG helper – shows all IDs present in CSV
    """
    ensure_csv_exists()

    ids = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("estimation_id", "").strip()
            if eid:
                ids.append(eid)
    return ids


def update_actual_effort(
    estimation_id,
    actual_grooming_effort,
    actual_implementation_effort
):
    rows = []
    found = False

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["estimation_id"] == estimation_id:
                found = True

                # -----------------------------
                # Actuals
                # -----------------------------
                actual_final = actual_grooming_effort + actual_implementation_effort

                row["actual_grooming_effort"] = actual_grooming_effort
                row["actual_implementation_effort"] = actual_implementation_effort
                row["actual_final_effort"] = actual_final

                # -----------------------------
                # Accuracy calculation
                # -----------------------------
                predicted_final = float(row.get("predicted_final_effort", 0) or 0)

                error_hours = actual_final - predicted_final

                if actual_final > 0:
                    accuracy = max(
                        0,
                        round(100 - (abs(error_hours) / actual_final) * 100, 2)
                    )
                else:
                    accuracy = ""

                if error_hours > 0:
                    over_under = "Underestimated"
                elif error_hours < 0:
                    over_under = "Overestimated"
                else:
                    over_under = "Accurate"

                row["accuracy_percent"] = accuracy
                row["error_hours"] = round(error_hours, 2)
                row["over_under"] = over_under

                # -----------------------------
                # Validation flag
                # -----------------------------
                row["validated"] = "yes"

            rows.append(row)

    if not found:
        raise ValueError(f"Estimation ID not found: {estimation_id}")

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

import csv

def get_estimation_by_id(estimation_id):
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["estimation_id"] == estimation_id:
                return row
    return None
