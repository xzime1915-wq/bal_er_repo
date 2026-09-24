import os
import shutil
import subprocess
from pathlib import Path

import psutil
import pyautogui

pyautogui.FAILSAFE = True

APP_ALIASES: dict[str, str] = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "vscode": "code",
    "code": "code",
    "edge": "msedge",
    "firefox": "firefox",
    "spotify": "spotify",
    "discord": "discord",
}


def open_application(name: str) -> str:
    key = name.strip().lower()
    target = APP_ALIASES.get(key, key)
    try:
        if target == "chrome":
            subprocess.Popen(
                ["cmd", "/c", "start", "", "chrome"],
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif target in ("wt", "powershell", "cmd"):
            subprocess.Popen(["cmd", "/c", "start", target], shell=False)
        else:
            os.startfile(target)  # type: ignore[attr-defined]
        return f"Opened: {name}"
    except Exception as e:
        return f"Could not open {name}: {e}"


def close_application(name: str) -> str:
    key = name.strip().lower()
    proc_name = APP_ALIASES.get(key, key)
    if not proc_name.endswith(".exe"):
        proc_name = f"{proc_name}.exe"
    killed = 0
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and p.info["name"].lower() == proc_name.lower():
                p.terminate()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return f"Closed {killed} process(es) matching {name}" if killed else f"No running process found for {name}"


def run_shell_command(command: str) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return out.strip() or f"Exit code: {r.returncode}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60s"
    except Exception as e:
        return f"Command failed: {e}"


def set_volume(level: int) -> str:
    level = max(0, min(100, level))
    script = f"(New-Object -ComObject WScript.Shell).SendKeys([char]173); "
    script += f"$obj = New-Object -ComObject WScript.Shell; "
    script += f"1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}; "
    script += f"$steps = [math]::Round({level}/2); "
    script += f"1..$steps | ForEach-Object {{ $obj.SendKeys([char]175) }}"
    return run_shell_command(script)


def take_screenshot(save_dir: str | None = None) -> str:
    folder = Path(save_dir) if save_dir else Path.home() / "Pictures" / "SENZ"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"senz_{int(__import__('time').time())}.png"
    img = pyautogui.screenshot()
    img.save(path)
    return str(path)


def list_directory(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"Path not found: {path}"
    items = []
    for item in sorted(p.iterdir())[:100]:
        kind = "dir" if item.is_dir() else "file"
        items.append(f"[{kind}] {item.name}")
    return "\n".join(items) if items else "(empty)"


def create_folder(path: str) -> str:
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return f"Created folder: {p}"


def move_path(src: str, dest: str) -> str:
    s, d = Path(src).expanduser(), Path(dest).expanduser()
    shutil.move(str(s), str(d))
    return f"Moved {s} -> {d}"


def search_files(root: str, pattern: str, limit: int = 20) -> str:
    root_path = Path(root).expanduser()
    if not root_path.exists():
        return f"Root not found: {root}"
    matches = []
    for p in root_path.rglob(pattern):
        matches.append(str(p))
        if len(matches) >= limit:
            break
    return "\n".join(matches) if matches else "No matches"
