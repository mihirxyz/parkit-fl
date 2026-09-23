# Evaluation Plan

## Research questions

- How accurately does the platform classify parking availability across structured and unstructured environments?
- How does federated training compare with isolated local training and centrally trained reference models?
- What is the communication, latency, and resource cost of federated rounds?
- How resilient is availability estimation under sparse, delayed, or heterogeneous observations?

## Metrics

### Availability detection

Report precision, recall, F1 score, balanced accuracy, confusion matrices, and calibration where probabilities are emitted. Stratify results by parking environment, occupancy level, lighting or weather proxy where available, and observation density.

### Federated learning

Report global validation performance per communication round, client-level performance distribution, convergence rounds, model-update size, total transmitted bytes, participation rate, and local training duration.

### Privacy and robustness

Document the data retained by clients and the coordinator, test reconstruction exposure where methods are available, and evaluate outcomes with dropped clients, non-independent client data, stale updates, and adversarial or low-quality updates.

## Centralized baseline results

The centralized PyTorch MLP classifier achieves **99.47% test accuracy** on the SUMO-simulated dataset with strong per-class performance:
- **Moving class (minority, 27%):** 100% precision, 98% recall, F1=0.99
- **Parked class (majority, 73%):** 99.3% precision, 100% recall, F1=0.996

This high accuracy reflects the fact that SUMO-simulated sensor features—especially GPS speed—are **highly separable by design**. Parked vehicles have near-zero speed with minimal synthetic noise, while moving vehicles exhibit distinctly higher speed. This establishes a **strong upper-bound baseline** for ideal sensor conditions.

However, **real-world sensor data is significantly harder to classify** due to GPS drift, ambiguous slow-rolling states (vehicles crawling in traffic or parking lots), high measurement noise, and temporal lags. The simulation-to-reality gap is a known limitation of purely synthetic evaluation. This project addresses this gap through a separate **real-world field-test evaluation** (see [Field-Test Evaluation](#field-test-evaluation) section below) that measures classifier performance on actual deployed vehicles with real sensor streams, capturing the messiness of production environments and validating whether the privacy-federated approach maintains accuracy under realistic conditions.

## Simulation-derived dataset

The baseline simulator scenario contains a small road grid, four parking areas, 200 vehicle trips, and a 3,600-second horizon. Parking labels originate from explicit SUMO parking-area stops. GPS speed, BLE RSSI, and IMU magnitude are derived from vehicle state using bounded measurement noise and a fixed seed. This makes the dataset more traceable than independently sampled feature vectors, while remaining synthetic and unsuitable as proof of real-world sensor performance.

## Reproducibility

Version scenario definitions, fix and record random seeds, preserve dependency versions, describe hardware and runtime configuration, and keep a separate held-out evaluation set. Do not include raw location traces or other sensitive observations in published artifacts. The generated SUMO CSV is excluded from version control and can be recreated with `python -m app.simulation.run_simulation`.
