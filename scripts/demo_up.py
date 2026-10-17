"""Start the Kairos demo: API + farmer + advisor apps (8000), Streamlit advisor dashboard (8501), Flask agronomist review (5050)."""
import os
import socket
import subprocess
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def busy(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    taken = [p for p in (8000, 8501, 5050) if busy(p)]
    if taken:
        sys.exit(f"Port(s) {', '.join(map(str, taken))} already in use: the demo is probably already running (open the URLs below), "
                 "or run `make demo-down` first, then `make demo-up`.\n  http://localhost:8000/farmer/  http://localhost:8501  http://localhost:5050")
    ip = lan_ip()
    print(f"""
Kairos demo
  Farmer app (iPhone)          http://{ip}:8000/farmer/
  Advisor app (iPhone)         http://{ip}:8000/advisor/
  Advisor dashboard (desktop)  http://localhost:8501
  Agronomist scenario review   http://localhost:5050
  API docs                     http://localhost:8000/docs
""", flush=True)
    dash = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "demo/dashboard_app.py"), "--server.port", "8501", "--server.headless", "true",
                             "--browser.gatherUsageStats", "false"], env={**os.environ, "KAIROS_API": "http://localhost:8000"},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    agro = subprocess.Popen([sys.executable, str(ROOT / "agronomist/app.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        uvicorn.run("kairos.api.main:app", host="0.0.0.0", port=8000, log_level="warning")
    finally:
        dash.terminate()
        agro.terminate()
        from kairos.assist import llm

        llm.unload()
