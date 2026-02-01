import csv
import os
from datetime import datetime

CSV_PATH = "data/effort_estimations.csv"


def ensure_csv_exists(fieldnames):
    """Create CSV with header if it doesn't exist"""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    if not os.path.isfile(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()


def append_estimation(row):
    """Append a new estimation row"""
    ensure_csv_exists(row.keys())

    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)


def update_actual_effort(
    estimation_id,
    actual_grooming,
    actual_implementation
):
    """Update actual effort and compute accuracy"""
    rows = []

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["estimation_id"] == estimation_id:
                actual_final = float(actual_grooming) + float(actual_implementation)
                predicted_final = float(row["predicted_final_effort"])

                error = actual_final - predicted_final
                accuracy = round(
                    (1 - abs(error) / actual_final) * 100, 2
                ) if actual_final != 0 else 0

                row.update({
                    "actual_grooming_effort": actual_grooming,
                    "actual_implementation_effort": actual_implementation,
                    "actual_final_effort": actual_final,
                    "error_hours": error,
                    "accuracy_percent": accuracy,
                    "validated": True,
                    "last_updated": datetime.now().isoformat()
                })

            rows.append(row)

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def delete_estimation(estimation_id):
    """Delete a row by estimation_id"""
    rows = []

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["estimation_id"] != estimation_id:
                rows.append(row)

    if not rows:
        return

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
