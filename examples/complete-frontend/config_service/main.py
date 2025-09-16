import os
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = FastAPI(title="EDPMT Configuration Service")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConfigUpdate(BaseModel):
    backend_ws_url: str = Field(..., alias="BACKEND_WS_URL")
    backend_http_url: str = Field(..., alias="BACKEND_HTTP_URL")
    update_interval: int = Field(..., alias="UPDATE_INTERVAL")
    enable_logging: bool = Field(..., alias="ENABLE_LOGGING")
    hardware_mode: str = Field(..., alias="HARDWARE_MODE")

    class Config:
        allow_population_by_field_name = True

@app.get("/api/config", response_model=Dict[str, Any])
async def get_config():
    """Get current configuration"""
    return {
        "BACKEND_WS_URL": os.getenv("BACKEND_WS_URL"),
        "BACKEND_HTTP_URL": os.getenv("BACKEND_HTTP_URL"),
        "UPDATE_INTERVAL": int(os.getenv("UPDATE_INTERVAL", 1000)),
        "ENABLE_LOGGING": os.getenv("ENABLE_LOGGING", "true").lower() == "true",
        "HARDWARE_MODE": os.getenv("HARDWARE_MODE", "simulator"),
    }

@app.put("/api/config")
async def update_config(update: ConfigUpdate):
    """Update configuration"""
    try:
        # Update .env file
        updates = {
            "BACKEND_WS_URL": update.backend_ws_url,
            "BACKEND_HTTP_URL": update.backend_http_url,
            "UPDATE_INTERVAL": str(update.update_interval),
            "ENABLE_LOGGING": str(update.enable_logging).lower(),
            "HARDWARE_MODE": update.hardware_mode,
        }

        # Write changes to .env file
        for key, value in updates.items():
            set_key(env_path, key, value, quote_mode="never")
        
        # Reload environment variables
        load_dotenv(env_path, override=True)
        
        return {"status": "success", "message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
