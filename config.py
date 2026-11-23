
import os
import platform
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str
    max_steps: int = 30
    screenshot_max_dimension: int = 1600
    screenshot_quality: int = 80
    action_delay: float = 0.3

    @classmethod
    def load(cls):
        api_key = os.getenv("AI_API_KEY", "").strip()
        base_url = os.getenv(
            "AI_BASE_URL",
            "https://ai.hackclub.com/proxy/v1"
        ).strip()
        model = os.getenv(
            "AI_MODEL",
            "openai/gpt-4o-mini"
        ).strip()

        if not api_key:
            raise ValueError("AI_API_KEY is missing from .env")

        if not base_url or not model:
            raise ValueError("AI_BASE_URL and AI_MODEL are required")

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model
        )


def detect_platform():
    system = platform.system()

    if system == "Linux":
        if os.getenv("WAYLAND_DISPLAY"):
            return "linux-wayland"

        if os.getenv("DISPLAY"):
            return "linux-x11"

        return "linux-unknown"

    if system == "Windows":
        return "windows"

    if system == "Darwin":
        return "macos"

    return "unknown"


config = Config.load()
PLATFORM = detect_platform()
SCREENSHOTS_DIR = ROOT / "screenshots"
MEMORY_FILE = ROOT / "memory.json"

SCREENSHOTS_DIR.mkdir(exist_ok=True)
