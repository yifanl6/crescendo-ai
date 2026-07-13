import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("CRESCENDO_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_officers() -> dict:
    path = DATA_DIR / "officers.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


@dataclass
class Config:
    slack_bot_token: str = field(default_factory=lambda: os.getenv("SLACK_BOT_TOKEN", ""))
    slack_app_token: str = field(default_factory=lambda: os.getenv("SLACK_APP_TOKEN", ""))
    slack_signing_secret: str = field(default_factory=lambda: os.getenv("SLACK_SIGNING_SECRET", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    meeting_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("MEETING_CONFIDENCE_THRESHOLD", "0.6"))
    )
    data_dir: Path = DATA_DIR
    officers: dict = field(default_factory=_load_officers)


config = Config()
