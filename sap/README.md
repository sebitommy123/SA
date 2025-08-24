# SAP (SA Provider Library)

Utilities to build SA-compliant providers easily. You focus on collecting data; SAP handles interval caching and serving it over a tiny HTTP API the SA Shell understands.

## Install

```bash
pip install -r requirements.txt  # ensures Flask
```

## Quickstart

```python
# example_provider.py
from sap import SAPServer, make_object, timestamp, link
from datetime import datetime

# Your heavy function: return a list of SA JSON objects (dicts)
def fetch_data():
    objs = [
        make_object(
            id="emp_001",
            types=["person", "employee"],
            source="my_system",
            name="Alice",
            hired_at=timestamp(datetime.utcnow()),
            profile=link(".filter(.equals(.get_field('name'), 'Alice'))", "Alice's records"),
        )
    ]
    return objs

server = SAPServer(
    provider=dict(name="My Provider", description="Demo provider"),  # or ProviderInfo(...)
    fetch_fn=fetch_data,
    interval_seconds=300,
)

if __name__ == "__main__":
    server.run(port=8080)
```

Endpoints provided:
- GET /hello → provider info `{ name, mode: "ALL_AT_ONCE", description, version }`
- GET /all_data → cached list of SA objects

## Notes
- `interval_seconds` controls how often `fetch_fn` runs. Results are cached and served fast.
- Use `make_object` and helpers (`timestamp`, `link`) to avoid managing `__id__`, `__source__`, `__types__` and `__sa_type__` by hand.