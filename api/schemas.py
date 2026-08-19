# ╔════════════════════════════════════════════════════════════╗
# ║ 🚚 IMPORTS
# ╚════════════════════════════════════════════════════════════╝
from typing import List
from pydantic import BaseModel

# ╔════════════════════════════════════════════════════════════╗
# ║ 📝 SCHEMAS
# ╚════════════════════════════════════════════════════════════╝


class PropertyInput(BaseModel):
    """
    Prediction request structure.
    """

    bed: int
    bath: int
    city: str
    state: str
    house_size: float
    prev_sold_year: int


class PredictionResponse(BaseModel):
    """
    Prediction response structure.
    """

    prediction: float


class PropertyBachInput(BaseModel):
    """
    Batch prediction request structure.
    """

    data: List[PropertyInput]


class ModelInfo(BaseModel):
    """
    Model info structure.
    """

    model_name: str
    model_type: str
    model_length: int
    model_features: list[str]
    model_description: str
    model_r2: float
    model_mae: float
    model_mse: float
    model_rmse: float
    model_max_error: float


class User(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
