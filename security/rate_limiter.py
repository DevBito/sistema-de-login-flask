import time
from functools import wraps
from flask import request, abort

# Dicionário simples para armazenar informações de visitantes
visitors = {}

def rate_limit(limit, per):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr
            current_time = time.time()
            visitor = visitors.get(ip, {"count": 0, "start": current_time})
            if current_time - visitor["start"] > per:
                visitor = {"count": 0, "start": current_time}
            visitor["count"] += 1
            visitors[ip] = visitor
            if visitor["count"] > limit:
                abort(429, description="Muitas requisições, tente novamente mais tarde.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
