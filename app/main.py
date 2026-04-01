import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, summary, transactions


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Finance Tracking API",
    description="""
Personal finance: CRUD, filters, summaries, roles.

**Auth (recommended):** `POST /auth/register` then `POST /auth/login` — use **Authorize** with **HTTP Bearer** token.

**Dev fallback:** `X-Role` header (`viewer` / `analyst` / `admin`), or omit for **admin**.

**Roles:**
- `viewer` — list & get (no filters); `GET /summary/viewer`
- `analyst` — filters + `GET /summary`
- `admin` — full CRUD
    """,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "message": "Validation failed",
        },
    )


app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(summary.router)

_frontend_dist = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)
if os.path.isdir(_frontend_dist):
    app.mount(
        "/ui",
        StaticFiles(directory=_frontend_dist, html=True),
        name="frontend",
    )


@app.get("/")
def root():
    out = {
        "message": "Finance Tracking API",
        "docs": "/docs",
        "health": "/health",
        "auth_register": "/auth/register",
        "auth_login": "/auth/login",
        "tip": "JWT: login then Authorize Bearer token, or X-Role header / omit for admin demo",
    }
    if os.path.isdir(_frontend_dist):
        out["ui"] = "/ui/"
    return out


@app.get("/health")
def health():
    return {"status": "ok"}
