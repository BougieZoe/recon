"""
RECON Person Client — importable by Band agents, 3DP Agent, and other tools.

Usage:
    from recon.person_client import ReconClient

    client = ReconClient()
    result = await client.analyze("Toki Hamasaki", website="example.com")
    # result is the full intent map dict

    # With streaming callbacks:
    def on_source(name, status, text_length):
        print(f"  {name}: {status}")

    def on_warning(msg):
        print(f"  ⚠ {msg}")

    result = await client.analyze("Toki Hamasaki", on_source=on_source, on_warning=on_warning)
"""

import asyncio
import json
import os
import threading
from typing import Callable, Optional


class ReconClient:
    """Client for the RECON Person API server.

    Connects to the local API server (auto-started if needed).
    Can also be configured to connect to a remote server.
    """

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        self.host = host
        self._port = port

    @property
    def port(self) -> int:
        if self._port is None:
            from .person_api_server import get_server_port, ensure_server
            p = get_server_port()
            if p is None:
                p = ensure_server()
            self._port = p
        return self._port

    @port.setter
    def port(self, value: int):
        self._port = value

    def _url(self, path: str) -> str:
        return f"http://{self.host}:{self.port}{path}"

    def analyze_sync(
        self,
        target: str = "",
        website: str = "",
        on_source: Optional[Callable] = None,
        on_warning: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> dict:
        """Synchronous version — blocks until analysis completes."""
        import httpx

        resp = httpx.post(self._url("/api/analyze"), json={"target": target, "website": website}, timeout=10)
        resp.raise_for_status()
        sid = resp.json()["session_id"]

        result = None

        with httpx.Client(timeout=60) as client:
            with client.stream("GET", self._url(f"/api/stream/{sid}")) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        msg = json.loads(line[6:])
                        t = msg.get("type")
                        if t in ("source_status", "source_update") and on_source:
                            on_source(msg.get("source", "?"), msg.get("status", "done"), msg.get("text_length", 0))
                        elif t == "warning" and on_warning:
                            on_warning(msg.get("message", ""))
                        elif t == "analysis_complete":
                            result = msg.get("result", {})
                            break
                        elif t == "error" and on_error:
                            on_error(msg.get("message", ""))
                            break

        return result or {}

    async def analyze(
        self,
        target: str = "",
        website: str = "",
        on_source: Optional[Callable] = None,
        on_warning: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> dict:
        """Async version — await to get the full intent map."""
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self._url("/api/analyze"), json={"target": target, "website": website})
            resp.raise_for_status()
            sid = resp.json()["session_id"]

        result = None
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("GET", self._url(f"/api/stream/{sid}")) as r:
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        msg = json.loads(line[6:])
                        t = msg.get("type")
                        if t in ("source_status", "source_update") and on_source:
                            on_source(msg.get("source", "?"), msg.get("status", "done"), msg.get("text_length", 0))
                        elif t == "warning" and on_warning:
                            on_warning(msg.get("message", ""))
                        elif t == "analysis_complete":
                            result = msg.get("result", {})
                            break
                        elif t == "error" and on_error:
                            on_error(msg.get("message", ""))
                            break

        return result or {}

    def history(self) -> list:
        """Return last 10 analysis entries from the server."""
        import httpx
        resp = httpx.get(self._url("/api/history"), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        """Check if server is running."""
        import httpx
        try:
            resp = httpx.get(self._url("/api/health"), timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {"status": "unreachable"}
