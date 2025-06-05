import os
import gc
import psutil
import torch
import logging
from functools import wraps

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def log_memory_usage(func_name):
    """Log memory usage before and after function execution"""
    memory_before = get_memory_usage()
    logging.info(f"Memory before {func_name}: {memory_before:.2f} MB")
    return memory_before

def cleanup_memory():
    """Aggressive memory cleanup"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def memory_monitor(func):
    """Decorator to monitor memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        memory_before = log_memory_usage(func.__name__)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            cleanup_memory()
            memory_after = get_memory_usage()
            logging.info(f"Memory after {func.__name__}: {memory_after:.2f} MB (diff: {memory_after - memory_before:+.2f} MB)")
    
    return wrapper

def check_memory_limit(limit_mb=450):
    """Check if we're approaching memory limit"""
    current = get_memory_usage()
    if current > limit_mb:
        logging.warning(f"Memory usage high: {current:.2f} MB (limit: {limit_mb} MB)")
        cleanup_memory()
        return True
    return False

def optimize_torch_for_cpu():
    """Set PyTorch optimizations for CPU-only inference"""
    torch.set_num_threads(1)  # Use single thread to save memory
    torch.set_num_interop_threads(1)
    
    # Disable autograd for inference
    torch.set_grad_enabled(False)
    
    # Set memory management
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1' 