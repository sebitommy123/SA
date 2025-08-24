#!/usr/bin/env python3
"""
Simple mock provider for testing the SA Query Language Shell.

This server starts 1 provider on port 5042 that returns one simple object.
"""

from flask import Flask, jsonify
import threading
import time

# Simple test object
import json
import os

SIMPLE_OBJECTS_FILE = os.environ.get("SIMPLE_OBJECTS_FILE", os.path.join(os.path.dirname(__file__), "resources", "simple_objects.json"))

def get_simple_objects():
    """Read the simple objects from a file on every request."""
    with open(SIMPLE_OBJECTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def create_simple_app():
    """Create a Flask app for the simple provider."""
    app = Flask("simple_provider")
    
    @app.route('/hello')
    def hello():
        """Provider information endpoint."""
        return jsonify({
            "name": "Simple Provider",
            "mode": "ALL_AT_ONCE",
            "description": "Simple provider with one test object",
            "version": "1.0.0"
        })
    
    @app.route('/all_data')
    def all_data():
        """Data endpoint that returns the single SAObject."""
        return jsonify(get_simple_objects())
    
    @app.route('/')
    def root():
        """Root endpoint with basic info."""
        return jsonify({
            "service": "Simple Provider",
            "endpoints": {
                "/hello": "Provider information",
                "/all_data": "Single SAObject data"
            },
            "status": "running"
        })
    
    return app

def start_simple_provider():
    """Start the simple provider server in a separate thread."""
    app = create_simple_app()
    port = 5042
    
    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Give the server a moment to start
    time.sleep(0.5)
    print(f"✓ Started Simple Provider on port {port}")
    
    return thread

if __name__ == '__main__':
    print("🚀 Starting Simple Mock Provider...")
    print("=" * 40)
    print("This will start 1 provider on port 5042")
    print()
    
    # Start the provider
    thread = start_simple_provider()
    
    print()
    print("✅ Provider is now running!")
    print("=" * 40)
    print("Provider URL for providers.txt:")
    print(f"  http://localhost:5042 - Simple Provider (1 object)")
    print()
    print("Press Ctrl+C to stop the provider")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down provider...")
        print("Goodbye!") 