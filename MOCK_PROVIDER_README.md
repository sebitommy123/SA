# Mock Provider for SA Query Language Shell

This is a mock provider server that simulates a real SA provider for testing the shell.

## What It Provides

The mock provider serves two required endpoints:

1. **`/hello`** - Returns provider information:
   ```json
   {
     "name": "Mock SA Provider",
     "mode": "ALL_AT_ONCE",
     "description": "A mock provider for testing the SA Query Language Shell",
     "version": "1.0.0"
   }
   ```

2. **`/all_data`** - Returns sample SAObject data:
   ```json
   [
     {
       "__types__": ["person", "employee"],
       "__id__": "emp_001",
       "__source__": "hr_database",
       "name": "John Doe",
       "department": "Engineering",
       "salary": 75000,
       "hire_date": "2023-01-15"
     },
     // ... more objects
   ]
   ```

## Sample Data

The mock provider includes 5 sample objects:
- 2 employees (person + employee types)
- 1 customer (person + customer type)  
- 1 software product (product + software type)
- 1 hardware product (product + hardware type)

## How to Use

### 1. Install Dependencies
```bash
pip install flask
```

### 2. Start the Mock Provider
```bash
python mock_provider.py
```

The server will start on `http://localhost:5000`

### 3. Test the Endpoints
```bash
# Test /hello endpoint
curl http://localhost:5000/hello

# Test /all_data endpoint  
curl http://localhost:5000/all_data

# Test root endpoint
curl http://localhost:5000/
```

### 4. Run the SA Shell
In another terminal:
```bash
python -m sa.shell.shell
```

The shell will:
- Connect to the mock provider
- Load the provider info (name: "Mock SA Provider", mode: "ALL_AT_ONCE")
- Fetch all 5 sample objects
- Display "Fetched 5 total objects from providers"

## Stopping the Mock Provider

Press `Ctrl+C` in the terminal where the mock provider is running.

## Customization

You can modify the `SAMPLE_OBJECTS` list in `mock_provider.py` to add more objects or change the existing ones. Just make sure each object has the required fields:
- `__types__` (list of strings)
- `__id__` (string)
- `__source__` (string) 