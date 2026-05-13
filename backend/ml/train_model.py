"""Train models to predict rental yield and save the best one."""

from __future__ import annotations

import json
from inspect import signature
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_STATE = 42
TARGET_COLUMN = "rental_yield"


def _build_encoder() -> OneHotEncoder:
    """Handle sklearn versions that use different sparse arguments."""
    if "sparse_output" in signature(OneHotEncoder).parameters:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Return RMSE."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def main() -> None:
    """Train baseline and main models, then persist the best pipeline."""
    project_backend = Path(__file__).resolve().parents[1]
    dataset_path = project_backend / "data" / "uk_property_data.csv"
    model_output_path = project_backend / "models" / "rental_yield_model.pkl"
    metrics_output_path = project_backend / "models" / "training_metrics.json"
    model_output_path.parent.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. Run generate_dataset.py first."
        )

    data = pd.read_csv(dataset_path)

    feature_columns = [
        "region",
        "property_type",
        "bedrooms",
        "purchase_price",
        "monthly_rent",
        "crime_rate",
        "amenity_score",
        "hpi_growth",
        "distance_to_station",
    ]
    categorical_features = ["region", "property_type"]
    numeric_features = [col for col in feature_columns if col not in categorical_features]

    X = data[feature_columns]
    y = data[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", _build_encoder(), categorical_features),
            ("numeric", "passthrough", numeric_features),
        ]
    )

    # Baseline vs main model.
    candidate_models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=350,
            max_depth=14,
            min_samples_leaf=3,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    results: dict[str, dict[str, float]] = {}
    fitted_pipelines: dict[str, Pipeline] = {}

    for model_name, regressor in candidate_models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("regressor", regressor),
            ]
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        results[model_name] = {
            "rmse": _rmse(y_test.to_numpy(), predictions),
            "mae": float(mean_absolute_error(y_test, predictions)),
            "r2": float(r2_score(y_test, predictions)),
        }
        fitted_pipelines[model_name] = pipeline

    best_model_name = min(results, key=lambda model: results[model]["rmse"])
    best_pipeline = fitted_pipelines[best_model_name]

    joblib.dump(best_pipeline, model_output_path)

    training_summary = {
        "selected_model": best_model_name,
        "metrics": results,
        "dataset_path": str(dataset_path),
        "model_path": str(model_output_path),
    }
    metrics_output_path.write_text(json.dumps(training_summary, indent=2), encoding="utf-8")

    print("Model comparison (test set):")
    for name, metric_values in results.items():
        print(
            f"- {name}: RMSE={metric_values['rmse']:.5f}, "
            f"MAE={metric_values['mae']:.5f}, R2={metric_values['r2']:.4f}"
        )
    print(f"Selected model: {best_model_name}")
    print(f"Saved model to: {model_output_path}")
    print(f"Saved metrics to: {metrics_output_path}")


if __name__ == "__main__":
    main()

