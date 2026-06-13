1. "C:\Users\TYSON\AppData\Local\pypoetry\Cache\virtualenvs\tim-rf3smOIg-py3.13\Scripts\activate.ps1" ------------> activate venv command

2.  "python -m backend.main" --------------------> To start the backend application (FAST API)

3.  "python -m client.run"   --------------------> To start the frontend  ui application 

Note: the client app now uses `CLIENT_DATABASE_URL` for its own database. If this is not set, it falls back to a local SQLite file (`client.db`).
