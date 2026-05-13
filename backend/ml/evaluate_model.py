"""Evaluate the saved model and generate simple charts."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
TARGET_COLUMN = "rental_yield"


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Return RMSE."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def _get_feature_importance(model_pipeline, feature_names: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Get feature scores from tree importances or linear coefficients."""
    regressor = model_pipeline.named_steps["regressor"]

    if hasattr(regressor, "feature_importances_"):
        importances = np.asarray(regressor.feature_importances_, dtype=float)
    elif hasattr(regressor, "coef_"):
        coefs = np.asarray(regressor.coef_, dtype=float)
        if coefs.ndim > 1:
            coefs = coefs.ravel()
        importances = np.abs(coefs)
    else:
        raise ValueError("Model does not expose feature importance or coefficients.")

    return feature_names, importances


def main() -> None:
    """Run evaluation on a holdout split and save outputs."""
    project_backend = Path(__file__).resolve().parents[1]
    project_root = project_backend.parent

    dataset_path = project_backend / "data" / "uk_property_data.csv"
    model_path = project_backend / "models" / "rental_yield_model.pkl"
    evaluation_dir = project_root / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = evaluation_dir / "model_metrics.json"
    scatter_plot_path = evaluation_dir / "predicted_vs_actual.png"
    importance_plot_path = evaluation_dir / "feature_importance.png"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. Run generate_dataset.py first."
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. Run train_model.py first."
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

    X = data[feature_columns]
    y = data[TARGET_COLUMN]

    # Use the same split setup as training.
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    model_pipeline = joblib.load(model_path)
    y_pred = model_pipeline.predict(X_test)

    metrics = {
        "rmse": _rmse(y_test.to_numpy(), y_pred),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Predicted vs actual scatter.
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, y_pred, alpha=0.45)
    min_axis = min(float(y_test.min()), float(y_pred.min()))
    max_axis = max(float(y_test.max()), float(y_pred.max()))
    plt.plot([min_axis, max_axis], [min_axis, max_axis], linestyle="--")
    plt.xlabel("Actual Rental Yield")
    plt.ylabel("Predicted Rental Yield")
    plt.title("Predicted vs Actual Rental Yield")
    plt.tight_layout()
    plt.savefig(scatter_plot_path, dpi=180)
    plt.close()

    # Top feature importances.
    preprocessor = model_pipeline.named_steps["preprocessor"]
    transformed_feature_names = preprocessor.get_feature_names_out()
    names, scores = _get_feature_importance(model_pipeline, transformed_feature_names)

    top_n = min(15, len(scores))
    top_indices = np.argsort(scores)[-top_n:]
    top_names = names[top_indices]
    top_scores = scores[top_indices]

    plt.figure(figsize=(10, 7))
    plt.barh(top_names, top_scores)
    plt.xlabel("Importance Score")
    plt.ylabel("Features")
    plt.title("Top Feature Importances")
    plt.tight_layout()
    plt.savefig(importance_plot_path, dpi=180)
    plt.close()

    print("Evaluation complete.")
    print(f"Metrics saved to: {metrics_path}")
    print(f"Predicted vs actual plot saved to: {scatter_plot_path}")
    print(f"Feature importance plot saved to: {importance_plot_path}")


if __name__ == "__main__":
    main()

