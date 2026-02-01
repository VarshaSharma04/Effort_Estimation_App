import uuid
from datetime import datetime
from csv_manager import append_estimation, list_estimation_ids

estimation_id = str(uuid.uuid4())

row = {
    "estimation_id": estimation_id,
    "feature_name": "Login Enhancement",
    "feature_description": "Add OTP-based login",
    "notes": "Security audit requirement",
    "estimated_by": "default_user",
    "estimation_timestamp": datetime.now().isoformat(),
    "model_version": "xgboost-v1",
    "predicted_grooming_effort": 12.5,
    "predicted_implementation_effort": 40,
    "predicted_final_effort": 52.5,
    "actual_grooming_effort": "",
    "actual_implementation_effort": "",
    "actual_final_effort": "",
    "accuracy_percent": "",
    "error_hours": "",
    "over_under": "",
    "confidence_level": "Medium",
    "validated": "false"
}

append_estimation(row)

print("✅ Appended estimation with ID:", estimation_id)
print("📌 Current IDs:", list_estimation_ids())
