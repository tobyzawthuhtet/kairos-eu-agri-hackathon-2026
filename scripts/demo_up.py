"""Start the Kairos demo: API + farmer + advisor apps (8000), Streamlit advisor dashboard (8501), Flask agronomist review (5050)."""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
PORTS = ROOT / "data/processed/demo/ports.json"


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


def free_port(want: int) -> int:
    """The wanted port if it is free, otherwise the next free one, so another app on 8000/5050 never blocks the demo."""
    port = want
    while busy(port):
        port += 1
    return port


def down() -> None:
    """Stop whatever the last `demo-up` started (ports are remembered in a small file) and unload the model."""
    ports = json.loads(PORTS.read_text()) if PORTS.exists() else {}
    for p in ports.values():
        subprocess.run(f"lsof -ti tcp:{p} -sTCP:LISTEN | xargs kill 2>/dev/null", shell=True, check=False)
    PORTS.unlink(missing_ok=True)
    from kairos.assist import llm

    llm.unload()
    print("demo stopped (model unloaded)")


if __name__ == "__main__":
    if "--down" in sys.argv:
        down()
        sys.exit()
    if PORTS.exists() and any(busy(p) for p in json.loads(PORTS.read_text()).values()):
        sys.exit("The demo is already running (URLs in the last output). Run `make demo-down` first.")
    api_port = free_port(int(os.environ.get("KAIROS_API_PORT", "8000")))
    dash_port = free_port(int(os.environ.get("KAIROS_DASH_PORT", "8501")))
    agro_port = free_port(int(os.environ.get("KAIROS_AGRO_PORT", "5050")))
    PORTS.parent.mkdir(parents=True, exist_ok=True)
    PORTS.write_text(json.dumps({"api": api_port, "dashboard": dash_port, "agronomist": agro_port}))
    ip = lan_ip()
    print(f"""
Kairos demo
  Farmer app (iPhone)          http://{ip}:{api_port}/farmer/
  Advisor app (iPhone)         http://{ip}:{api_port}/advisor/
  Advisor dashboard (desktop)  http://localhost:{dash_port}
  Agronomist scenario review   http://localhost:{agro_port}
  API docs                     http://localhost:{api_port}/docs
""", flush=True)
    dash = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "demo/dashboard_app.py"), "--server.port", str(dash_port),
                             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                            env={**os.environ, "KAIROS_API": f"http://localhost:{api_port}"}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    agro = subprocess.Popen([sys.executable, str(ROOT / "agronomist/app.py")], env={**os.environ, "KAIROS_AGRO_PORT": str(agro_port)},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        uvicorn.run("kairos.api.main:app", host="0.0.0.0", port=api_port, log_level="warning")
    finally:
        dash.terminate()
        agro.terminate()
        PORTS.unlink(missing_ok=True)
        from kairos.assist import llm

        llm.unload()
