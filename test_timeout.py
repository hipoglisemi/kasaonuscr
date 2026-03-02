import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")

def run_with_timeout(func, args=(), kwargs={}, timeout_duration=60):
    # Set the signal handler and a 60-second alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_duration)
    try:
        result = func(*args, **kwargs)
    finally:
        # Disable the alarm
        signal.alarm(0)
    return result
