"""
POST/health        → simple health check point.
"""

# ╔════════════════════════════════════════════════════════════╗
# ║ 🚚 IMPORTS
# ╚════════════════════════════════════════════════════════════╝
from core.settings import settings

# ╔════════════════════════════════════════════════════════════╗
# ║ 🌐 API
# ╚════════════════════════════════════════════════════════════╝
from fastapi import FastAPI


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ╔════════════════════════════════════════════════════════════╗
# ║ 🥷 MIDDLEWARES
# ╚════════════════════════════════════════════════════════════╝
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=10000)

# ╔════════════════════════════════════════════════════════════╗
# ║ 🛣️ ROUTERS
# ╚════════════════════════════════════════════════════════════╝
from api.model import model_predict, model_predict_batch, model_upload, model_info
from api.auth import user_login, refresh_token

# from api.auth import user_login, refresh_token

app.include_router(model_predict)
app.include_router(model_predict_batch)
app.include_router(model_upload)
app.include_router(model_info)
app.include_router(user_login)
app.include_router(refresh_token)


# ╔════════════════════════════════════════════════════════════╗
# ║ ⛑️ HEALTH CHECK
# ╚════════════════════════════════════════════════════════════╝
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "OK",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "model_loaded": hasattr(app.state, "model"),
    }
