import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# Generate Dataset
np.random.seed(42)

data = {
    "study_hours": np.random.uniform(1, 10, 500),
    "attendance": np.random.uniform(40, 100, 500),
    "previous_marks": np.random.uniform(30, 100, 500),
    "assignment_score": np.random.uniform(30, 100, 500),
    "sleep_hours": np.random.uniform(4, 10, 500)
}

df = pd.DataFrame(data)

# Calculate Final Marks
df["final_marks"] = (
    df["study_hours"] * 4 +
    df["attendance"] * 0.2 +
    df["previous_marks"] * 0.3 +
    df["assignment_score"] * 0.2 +
    df["sleep_hours"] * 1.5
)

df["final_marks"] = df["final_marks"].clip(0, 100)

# Save Dataset
df.to_csv("dataset.csv", index=False)

# Features and Target
X = df.drop("final_marks", axis=1)
y = df["final_marks"]

# Split Dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Model
model = LinearRegression()
model.fit(X_train, y_train)

# Predictions
predictions = model.predict(X_test)

# Evaluation
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("EduPredict Model Trained Successfully!")
print("Mean Absolute Error:", mae)
print("R2 Score:", r2)