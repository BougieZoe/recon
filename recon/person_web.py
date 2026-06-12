"""
RECON Person Web UI — thin wrapper around person_api_server.
The HTML/JS frontend calls /api/* endpoints directly on the same server.
"""

import os
import sys

from .person_api_server import run_person_server


def run_person_web(theme="green"):
    run_person_server(open_browser=True)
