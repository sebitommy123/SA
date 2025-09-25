
import traceback
import time
from sa.query_language.chain import Chain
from sa.core.object_list import ObjectList
from sa.query_language.parser import parse_query_into_querytype, run_query

def execute_query(query: str, context):
    """Execute a query string and return the result."""
    # Check if profiling is enabled
    try:
        from sa.query_language.operators import PROFILING_ENABLED, _profiling_collector
        if PROFILING_ENABLED:
            start_time = time.time()

            result = run_query(query, context)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Record the total query execution time
            _profiling_collector.record_operation("Total query execution", duration)
            
            # Display the profiling summary
            print(_profiling_collector.get_summary())
            _profiling_collector.reset()
            
            return result
    except ImportError:
        pass

    return run_query(query, context)
