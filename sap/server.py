from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Optional

from flask import Flask, jsonify

from .scheduler import IntervalCacheRunner


@dataclass
class ProviderInfo:
    name: str
    description: str
    version: str = "0.1.0"
    mode: str = "ALL_AT_ONCE"


class SAPServer:
    def __init__(
        self,
        provider: ProviderInfo | dict,
        fetch_fn: Callable[[], List[dict]],
        interval_seconds: float,
        run_immediately: bool = True,
    ) -> None:
        if isinstance(provider, dict):
            self.provider = ProviderInfo(
                name=provider.get("name", "SAP Provider"),
                description=provider.get("description", ""),
                version=provider.get("version", "0.1.0"),
                mode=provider.get("mode", "ALL_AT_ONCE"),
            )
        else:
            self.provider = provider
        self.runner = IntervalCacheRunner(fetch_fn=fetch_fn, interval_seconds=interval_seconds, run_immediately=run_immediately)
        self.app = Flask("sap-provider")
        self._configure_routes()

    def _configure_routes(self) -> None:
        app = self.app
        provider = self.provider
        runner = self.runner

        @app.route("/hello")
        def hello():
            return jsonify({
                "name": provider.name,
                "mode": provider.mode,
                "description": provider.description,
                "version": provider.version,
            })

        @app.route("/all_data")
        def all_data():
            return jsonify(runner.get_cached())

        @app.route("/")
        def root():
            return jsonify({
                "service": provider.name,
                "endpoints": {"/hello": "Provider information", "/all_data": "All SAObject data"},
                "status": "running",
            })

    def run(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False) -> None:
        self.runner.start()
        self.app.run(host=host, port=port, debug=debug)


def run_server(
    name: str,
    description: str,
    fetch_fn: Callable[[], List[dict]],
    interval_seconds: float,
    version: str = "0.1.0",
    mode: str = "ALL_AT_ONCE",
    host: str = "0.0.0.0",
    port: int = 8080,
    run_immediately: bool = True,
    debug: bool = False,
) -> None:
    server = SAPServer(ProviderInfo(name=name, description=description, version=version, mode=mode), fetch_fn=fetch_fn, interval_seconds=interval_seconds, run_immediately=run_immediately)
    server.run(host=host, port=port, debug=debug)