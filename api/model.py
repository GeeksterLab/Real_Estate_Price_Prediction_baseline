"""
POST/predict                → prediciton for 1 property
POST/predict-batch          → prediction for several properties
POST/upload                 → CSV upload
GET/model-info             → model loaded info
"""

# ╔════════════════════════════════════════════════════════════╗
# ║ 🚚 IMPORTS
# ╚════════════════════════════════════════════════════════════╝
import pandas as pd

from core.settings import settings

# ╔════════════════════════════════════════════════════════════╗
# ║ 🌐 API
# ╚════════════════════════════════════════════════════════════╝
from fastapi import APIRouter

model_predict = APIRouter()
model_predict_batch = APIRouter()
model_upload = APIRouter()
model_info = APIRouter()

# ╔════════════════════════════════════════════════════════════╗
# ║ 🛣️ ROUTERS
# ╚════════════════════════════════════════════════════════════╝
import csv

from io import StringIO
from fastapi import UploadFile, File, HTTPException, status, Depends

from api.schemas import PropertyInput, PropertyBachInput, PredictionResponse, ModelInfo

from api.utils import get_model, get_current_user


# ── PREDICITON ──────────────────────────────────────────────
@model_predict.post(
    "/prediction", response_model=PredictionResponse, tags=["Prediction"]
)
def prediction_price(
    data: PropertyInput,
    baseline=Depends(get_model),
    current_user: str = Depends(get_current_user),
) -> PredictionResponse:

    # ═════════════════════ Transform the data ═════════════════════
    df = pd.json_normalize(data.model_dump())

    # ═════════════════════ Send the data ═════════════════════
    prediction = baseline["model"].predict(df)[0]

    return PredictionResponse(prediction=prediction)


# ── PREDICITON BATCH ────────────────────────────────────────
@model_predict_batch.post("/prediction-batch", tags=["PredictionBatch"])
def prediction_price_batch(
    data: PropertyBachInput,
    baseline=Depends(get_model),
    current_user: str = Depends(get_current_user),
) -> list[PredictionResponse]:

    results = []

    for property in data.data:
        df = pd.json_normalize(property.model_dump())

        prediction = baseline["model"].predict(df)[0]

        results.append(PredictionResponse(prediction=prediction))

    return results


# ── UPLOAD ──────────────────────────────────────────────────
@model_upload.post("/upload", tags=["Upload"])
async def upload_csv(file: UploadFile = File(...)):
    data = []

    # Read file as bytes and decodes bytes into text stream
    file_bytes = await file.read()
    buffer = StringIO(file_bytes.decode("utf-8"))

    # Process CSV
    csvReader = csv.DictReader(buffer)
    for row in csvReader:
        data.append(row)

    # Close buffer and file
    buffer.close()
    await file.close()

    # Return JSON
    return data


# ── MODEL INFO ──────────────────────────────────────────────
@model_info.get("/model_info", response_model=ModelInfo, tags=["ModelInfo"])
def model_information(
    baseline=Depends(get_model),
    current_user: str = Depends(get_current_user),
) -> ModelInfo:

    # Is our model exist?
    if not settings.BASELINE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baseline model file not found.",
        )

    else:
        return ModelInfo(
            model_name=settings.BASELINE_PATH.name,
            model_type=baseline["type"],
            model_length=baseline["length"],
            model_features=baseline["features"],
            model_description="Baseline model for price prediction.",
            model_r2=round(baseline["metrics"]["R2"], 2),
            model_mae=round(baseline["metrics"]["MAE"], 2),
            model_mse=round(baseline["metrics"]["MSE"], 2),
            model_rmse=round(baseline["metrics"]["RMSE"], 2),
            model_max_error=round(baseline["metrics"]["MAX_ERROR"], 2),
        )
