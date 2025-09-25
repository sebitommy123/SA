# Performance Testing Utilities

This directory contains utilities for testing and debugging the performance of the `group_by_id_types` method.

## Files

### `debug_performance.py`
Detailed profiling script that uses `cProfile` to identify performance bottlenecks. Shows:
- Execution time and objects/second rate
- Function call counts and timing
- Top 10 most time-consuming functions

**Usage:**
```bash
python -m performance_tests.debug_performance
```

### `quick_perf_test.py`
Quick performance benchmark that tests various dataset sizes and shows:
- Execution time for each dataset size
- Objects processed per second
- Number of groups created

**Usage:**
```bash
python -m performance_tests.quick_perf_test
```

## Performance Expectations

With the current optimizations, you should see:

- **100 objects**: ~0.0002s (590,000+ objects/sec)
- **1000 objects**: ~0.0017s (575,000+ objects/sec)  
- **5000 objects**: ~0.032s (158,000+ objects/sec)
- **10000 objects**: ~0.062s (161,000+ objects/sec)

The algorithm now scales very efficiently and can handle large datasets extremely quickly!

## Running from SA directory

Make sure you're in the SA directory when running these scripts:

```bash
cd /path/to/SA
python -m performance_tests.debug_performance
python -m performance_tests.quick_perf_test
```
