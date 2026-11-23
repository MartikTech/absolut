def scroll(amount):
    amount = max(-10, min(10, int(amount)))

    if PLATFORM == "linux-wayland":
        run_command([
            "ydotool",
            "mousemove",
            "--wheel",
            "-x", "0",
            "-y", str(amount)
        ])
    else:
        pyautogui.scroll(amount)