from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.endpoints import router as api_router

# Initialize the FastAPI application
app = FastAPI(
    title="Urban Air Quality Intelligence API",
    description="Backend services for AQI Forecasting, Source Attribution, and Enforcement Prioritization.",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check():
    """Standard health check endpoint to verify API operational status."""
    return {
        "status": "Operational",
        "service": "AQI Predictor Backend"
    }


# ---------------------------------------------------------------------------
# Feature 4 (Citizen Health Advisory, multilingual) + Feature 5 (Multi-city)
# Owner: Bind. Mounts the advisory API (/advisory, /chat, /compare, /sources,
# /tts, /meta, /wards) into this unified backend and serves the citizen chat UI
# at /citizen. It reads the SAME data/source_attribution.csv contract as
# /api/v1/attribution, falling back to committed mock data when the CSV is absent
# — so it runs even before the ML CSVs land. Its own /health is shadowed by the
# system one above (harmless).
# ---------------------------------------------------------------------------
import os

from fastapi.responses import FileResponse

from backend.advisory_api import router as advisory_router

app.include_router(advisory_router, tags=["Citizen Advisory (F4/F5)"])


@app.get("/citizen", include_in_schema=False)
def citizen_ui():
    """Serve the WhatsApp-style citizen advisory chat UI."""
    ui = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "frontend", "advisory_demo.html")
    return FileResponse(ui)