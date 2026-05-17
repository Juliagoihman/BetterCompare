from fastapi import FastAPI
app = FastAPI()
# importiere alle admin routes aus main
from main import admin as _admin
app = _admin
