import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def wait_for_server(process, base_url):
    deadline = time.time() + 20
    with sync_playwright() as playwright:
        request = playwright.request.new_context()
        try:
            while time.time() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Django development server exited early.")
                try:
                    response = request.get(base_url, timeout=1000)
                    if response.status in {200, 302}:
                        return
                except Exception:
                    time.sleep(0.25)
        finally:
            request.dispose()
    raise RuntimeError("Django development server did not start in time.")


def run():
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        env = os.environ.copy()
        env.setdefault("DEBUG", "True")
        env["SQLITE_DATABASE_PATH"] = str(temp_path / "e2e.sqlite3")
        env["MEDIA_ROOT"] = str(temp_path / "media")

        subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], cwd=ROOT, env=env, check=True)
        subprocess.run([sys.executable, "manage.py", "load_sample_data"], cwd=ROOT, env=env, check=True)

        server = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        try:
            wait_for_server(server, base_url)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(f"{base_url}/login/")
                page.get_by_label("Username").fill("docy")
                page.get_by_label("Password").fill("V7qN4pX9rL2m")
                page.get_by_role("button", name="Login").click()

                expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
                page.get_by_role("link", name="Scans").click()
                expect(page.get_by_role("heading", name="Scans")).to_be_visible()

                page.get_by_placeholder("Search by patient, reason, or diagnosis").fill("Normal")
                page.get_by_role("button", name="Search").click()
                expect(page.get_by_role("cell", name="Normal finding").first).to_be_visible()

                page.get_by_role("link", name="Analytics").click()
                expect(page.locator("#age-chart svg")).to_be_visible()
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    run()
