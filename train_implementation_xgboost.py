import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# Load implementation dataset
df = pd.read_excel(
    "Effort_Estimation_Grooming_Implementation_FINAL.xlsx",
    sheet_name="Implementation"
)

# Separate inputs and output
X = df.drop(columns=["Feature_ID", "Final_Effort_Hours"])
y = df["Final_Effort_Hours"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# XGBoost model
model = XGBRegressor(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=7,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)

# Train
model.fit(X_train, y_train)

# Save model
joblib.dump(model, "impl_effort_model.pkl")

print("✅ Implementation XGBoost model trained & saved")
