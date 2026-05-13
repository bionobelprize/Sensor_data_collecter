from __future__ import annotations

import logging
from threading import Thread

from flask import Flask, jsonify

from sensor_collector.status import RuntimeStatus


def start_status_server(status: RuntimeStatus, host: str, port: int, logger: logging.Logger) -> Thread:
    app = Flask("sensor_collector_status")

    @app.get("/")
    def status_root():  # noqa: ANN202
        return jsonify(status.snapshot())

    @app.get("/health")
    def health():  # noqa: ANN202
        return jsonify({"ok": True, "service_state": status.snapshot()["service_state"]})

    def _run() -> None:
        logger.info("Starting status server on http://%s:%s", host, port)
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    thread = Thread(target=_run, name="status-server", daemon=True)
    thread.start()
    return thread
