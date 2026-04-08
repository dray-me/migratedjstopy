"""
Function Handler - Python equivalent of functionHandler.js
Handles scheduled functions with intervals, retries, and max executions.
"""
import asyncio
import os
import importlib.util
from core.logger import logger

# Store for active function tasks
_active_tasks = {}

class FunctionConfig:
    """Configuration for a scheduled function."""
    def __init__(self, **kwargs):
        self.once = kwargs.get('once', False)
        self.interval = kwargs.get('interval')  # in seconds
        self.retry_attempts = kwargs.get('retryAttempts', 3)
        self.max_execution = kwargs.get('maxExecution', float('inf'))
        self.initializer = kwargs.get('initializer', 0)  # delay before first run

async def load_function_from_file(file_path):
    """Load a function from a Python file."""
    try:
        spec = importlib.util.spec_from_file_location("function_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for the main function (should be named 'main' or 'run')
        func = getattr(module, 'main', None) or getattr(module, 'run', None)
        config = getattr(module, 'config', {})
        
        return func, config
    except Exception as e:
        logger.error(f"Failed to load function from {file_path}: {e}")
        return None, {}

def get_all_function_files(directory="functions"):
    """Get all Python files from the functions directory."""
    function_files = []
    functions_dir = os.path.join(os.getcwd(), directory)
    
    if not os.path.exists(functions_dir):
        return function_files
    
    for root, dirs, files in os.walk(functions_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                function_files.append(os.path.join(root, file))
    
    return function_files

async def handle_single_function(name, func, config_dict):
    """Handle a single function with scheduling configuration."""
    config = FunctionConfig(**config_dict)
    
    # Validate interval
    if config.interval is not None and not isinstance(config.interval, (int, float)):
        logger.error(f"Invalid interval for function {name}. Interval must be a number.")
        return
    
    # Initial delay
    if config.initializer:
        logger.info(f"Waiting {config.initializer} seconds before starting function {name}...")
        await asyncio.sleep(config.initializer)
    
    executions = 0
    retries = 0
    
    async def run_function():
        nonlocal executions, retries
        
        if executions >= config.max_execution:
            logger.info(f"Max executions reached for {name}.")
            if name in _active_tasks:
                _active_tasks[name].cancel()
            return
        
        try:
            logger.info(f"Executing function: {name}...")
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
            executions += 1
            retries = 0  # Reset retries on success
        except Exception as e:
            logger.error(f"Error executing function {name}: {e}")
            retries += 1
            if retries >= config.retry_attempts:
                logger.warning(f"Failed after {config.retry_attempts} retries for {name}.")
                if name in _active_tasks:
                    _active_tasks[name].cancel()
    
    if config.once:
        await run_function()
    elif config.interval:
        async def interval_loop():
            while True:
                await run_function()
                if executions < config.max_execution:
                    await asyncio.sleep(config.interval)
                else:
                    break
        
        task = asyncio.create_task(interval_loop())
        _active_tasks[name] = task
    else:
        # Run once if no interval specified
        await run_function()

async def load_and_run_functions(directory="functions"):
    """Load and run all functions from the functions directory."""
    function_files = get_all_function_files(directory)
    
    if not function_files:
        logger.info("No function files found.")
        return
    
    logger.success(f"Found {len(function_files)} function file(s).")
    
    for file_path in function_files:
        func, config = await load_function_from_file(file_path)
        if func:
            func_name = os.path.basename(file_path)[:-3]  # Remove .py
            await handle_single_function(func_name, func, config)

def stop_function(name):
    """Stop a running function by name."""
    if name in _active_tasks:
        _active_tasks[name].cancel()
        del _active_tasks[name]
        logger.info(f"Stopped function: {name}")

def stop_all_functions():
    """Stop all running functions."""
    for name, task in _active_tasks.items():
        task.cancel()
        logger.info(f"Stopped function: {name}")
    _active_tasks.clear()

# Example function file template
EXAMPLE_FUNCTION_TEMPLATE = '''"""
Example scheduled function for Discobase.
Save this file in the 'functions' directory.
"""

# Configuration for this function
config = {
    "once": False,           # Run only once
    "interval": 60,          # Run every 60 seconds
    "retryAttempts": 3,      # Retry 3 times on failure
    "maxExecution": 10,      # Stop after 10 executions (optional)
    "initializer": 5         # Wait 5 seconds before first run
}

async def main():
    """
    Main function to be executed.
    Can be async or sync.
    """
    print("Running scheduled function!")
    # Your code here

# For sync functions, use:
# def main():
#     print("Running scheduled function!")
'''
