# Parkit

Parkit is a privacy-preserving parking-availability platform designed around federated learning. It supports structured facilities and unstructured curbside or open-area parking through a shared spatial-grid abstraction.

## Repository layout

- `backend/`: FastAPI service, persistence, grid, machine-learning, and simulation boundaries.
- `mobile/`: Flutter client application workspace.
- `fl_clients/`: independently runnable federated-client processes.
- `docs/`: architecture and evaluation plans.

## Quick start

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API health endpoint is available at `GET /api/v1/health`.
