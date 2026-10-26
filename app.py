import os
from flask import Flask, jsonify

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "v1")

@app.get("/")
def home():
    return jsonify(app="secureflow-demo", version=VERSION)

@app.get("/health")
def health():
    return jsonify(status="ok")
