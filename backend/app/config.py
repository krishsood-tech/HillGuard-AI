from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE = f"sqlite:///{(BACKEND / 'data' / 'hillguard.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    demo_mode: bool = True
    database_url: str = DEFAULT_SQLITE
    jwt_secret: str = "change-this-to-a-long-random-string"
    jwt_expire_minutes: int = 720
    weather_api_key: str = ""
    weather_provider: str = "open-meteo"
    map_tile_url: str = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
    routing_api_key: str = ""
    osrm_url: str = "https://router.project-osrm.org"
    frontend_origin: str = "http://localhost:5173"
    max_upload_mb: int = 5
    emergency_imd_url: str = "https://mausam.imd.gov.in/"
    emergency_ndma_url: str = "https://ndma.gov.in/"
    emergency_hpsdma_url: str = "https://hpsdma.nic.in/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
