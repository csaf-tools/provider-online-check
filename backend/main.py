# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.router.router import router
import logging
import os
import sys

app = FastAPI(
    title="CSAF Provider Scan API",
    description="API for scanning CSAF providers",
    version=os.getenv("APP_VERSION"),
    docs_url=None,  # provided by the custom function custom_swagger_ui below
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

STATIC_DIR = Path(__file__).parent / "static" / "swagger-ui"
if os.path.isdir(STATIC_DIR):  # In production setups, with local static files
    app.mount("/api/static/swagger-ui", StaticFiles(directory=STATIC_DIR), name="swagger-ui-static")
    swagger_ui_kwargs = {
        "swagger_js_url": "/api/static/swagger-ui/swagger-ui-bundle.js",
        "swagger_css_url": "/api/static/swagger-ui/swagger-ui.css",
    }
else:
    # In development setups, just use the default URLs with externally hosted assets
    swagger_ui_kwargs = {}

@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="CSAF Provider Scan API",
        swagger_favicon_url="data:,",  # disables loading the favicon from an external source
        **swagger_ui_kwargs,
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(router, prefix="/api")


level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
