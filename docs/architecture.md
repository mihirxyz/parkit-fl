# Architecture

## Overview

Parkit separates externally visible API operations from storage, geospatial representation, model operations, and traffic-simulation adapters. This separation allows production data sources to replace simulation sources without changing availability consumers.

## Backend layers

- **API:** Versioned FastAPI routers validate requests and return stable response models.
- **Core:** Typed settings read only `PARKIT_`-prefixed environment variables.
- **Database:** SQLAlchemy manages persistence and session lifecycles. SQLite is the development default; the database URL is configurable for deployment.
- **Grid:** Geographic coordinates map deterministically to grid cells. A grid cell is the common representation for parking availability in both structured and unstructured settings.
- **ML:** Federated aggregation works on model state dictionaries, so raw device observations remain local to each client process.
- **Simulation:** Simulator adapters translate an external simulator's data into application-level observations. The included SUMO scenario models traffic trajectories and explicit parking-area stops before synthetic sensor features are derived.

## Federated-learning workflow

1. The coordinator publishes a global model version.
2. Each client trains locally on device-resident observations.
3. Each client submits a weighted model update, not raw observations.
4. The coordinator aggregates compatible updates using weighted FedAvg.
5. The coordinator evaluates and publishes a new model version.

Transport security, authentication, secure aggregation, and differential-privacy mechanisms are deployment concerns to be integrated at the client/coordinator boundary before real-world use.
