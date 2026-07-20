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