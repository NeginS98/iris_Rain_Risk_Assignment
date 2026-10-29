# IRIS-SIM-RAIN: Heavy Rainfall Data Processing

This project uses hourly rainfall data from the German Weather Service (DWD) to identify periods of heavy rainfall at weather stations.

It is designed for preliminary screening only and is **not intended for certified engineering design**.

## 1. Data Source

The project uses hourly precipitation data from the DWD Open Data archive.

- Source: DWD Climate Data Center (CDC)
- Data: Hourly precipitation observations
- Main fields: `STATIONS_ID`, `MESS_DATUM`, `QN_8`, and `R1`
- `R1` represents hourly rainfall in millimetres.
- `MESS_DATUM` contains the observation date and hour.
- `-999` represents a missing rainfall value.


## 2. Rainfall Classification

Each hourly observation is assigned a class based on the recorded rainfall amount.

| Class | Rainfall |
|---|---|
| `NO_DATA` | No valid rainfall value |
| `BELOW_THRESHOLD` | Less than 15 mm/h |
| `HEAVY` | 15 to less than 25 mm/h |
| `VERY_HEAVY` | 25 to less than 40 mm/h |
| `EXTREME` | 40 mm/h or more |

These thresholds can be changed in the configuration file. They are used for initial screening and should be checked against the relevant DWD warning guidance.

Observations with missing rainfall data are not classified as rainfall events.

## 3. How to Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the pipeline without writing to a database:

```bash
python -m iris_rain.cli --input "path/to/station_files/*.zip" --dry-run
```

Run the tests:

```bash
python -m pytest -q
```

To test database loading, configure the database settings in `.env` and start the staging database:

```bash
cp .env.example .env
docker compose up -d staging-db
docker compose run --rm loader
```

Do not commit `.env` or database passwords to Git.

## 4. Output

The pipeline produces:

- `out/quality_report.json`: a summary of data quality.
- `out/rejects.jsonl`: records that could not be processed.
- `iris_staging.heavy_rainfall_risk`: the staging table for classified observations.

The staging table uses the station ID and observation hour to identify each record. Running the pipeline again should not create duplicate records.

The code is intended to prevent writes outside the `iris_staging` schema.

## 5. Data Processing Rules

- The original station ID, observation time, rainfall amount, and quality level are retained.
- Missing or invalid rainfall values are not treated as zero.
- If multiple records exist for the same station and hour, the first record is kept and conflicting records are reported.
- Negative values other than the missing-data marker, and values above the configured maximum, are rejected.
- The same input data and configuration should produce the same classification results.

## 6. Limitations

This project uses rainfall measurements from individual weather stations. It does not calculate rainfall over an entire area, estimate return periods, or capture rainfall peaks shorter than one hour.

The classification is intended to help identify heavy-rainfall observations. It does not replace a detailed flood-risk assessment or engineering design.

## 7. Testing

The tests use a small sample file created for this project. They do not represent a complete validation against real DWD observations.

The download helper has not yet been fully tested against the live DWD server.

## 8. AI Assistance

AI assistance was used during parts of the coding and documentation process. The code was reviewed and modified as part of the project.

