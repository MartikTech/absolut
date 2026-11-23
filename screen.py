
import base64
import io
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import mss
import pytesseract
from PIL import Image

from config import (
    config,
    PLATFORM,
    SCREENSHOTS_DIR
)


def capture_native():
    if PLATFORM == "linux-wayland":
        filename = SCREENSHOTS_DIR / (
            f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        )

        commands = []

        if shutil.which("spectacle"):
            commands.append([
                "spectacle", "-b", "-n", "-o", str(filename)
            ])

        if shutil.which("grim"):
            commands.append(["grim", str(filename)])

        if shutil.which("gnome-screenshot"):
            commands.append([
                "gnome-screenshot", "-f", str(filename)
            ])

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=20
                )

                if result.returncode == 0 and filename.exists():
                    image = Image.open(filename).convert("RGB")
                    return image, filename

            except (OSError, subprocess.TimeoutExpired):
                pass

            filename.unlink(missing_ok=True)

        raise RuntimeError(
            "No working Wayland screenshot backend. "
            "Install Spectacle, grim or gnome-screenshot."
        )

    with mss.mss() as capture:
        monitor = capture.monitors[0]
        raw = capture.grab(monitor)

        image = Image.frombytes(
            "RGB",
            raw.size,
            raw.rgb
        )

    filename = SCREENSHOTS_DIR / (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    )

    image.save(filename, format="PNG")

    return image, filename


def capture_screen():
    image, filename = capture_native()

    width, height = image.size

    ocr = pytesseract.image_to_string(
        image,
        config="--psm 11"
    ).strip()[:15000]

    preview = image.copy()

    preview.thumbnail(
        (
            config.screenshot_max_dimension,
            config.screenshot_max_dimension
        ),
        Image.Resampling.LANCZOS
    )

    buffer = io.BytesIO()

    preview.save(
        buffer,
        format="JPEG",
        quality=config.screenshot_quality
    )

    return {
        "image": base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8"),
        "width": width,
        "height": height,
        "image_width": preview.width,
        "image_height": preview.height,
        "ocr": ocr,
        "screenshot_path": str(filename),
        "platform": PLATFORM
    }
