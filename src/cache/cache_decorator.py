import pickle
from functools import wraps
from typing import Callable, Any, Awaitable
from src.cache.client import redis_client


def redis_cache(key_builder: Callable[..., str], expire: int = 300):
    """
    Decorator for caching the result of an asynchronous function in Redis.

    Args:
        key_builder (Callable[..., str]): A function that generates a Redis key from the target function's arguments.
        expire (int, optional): Time-to-live (TTL) for the cache in seconds. Defaults to 300 seconds.

    Returns:
        Callable: A decorator that wraps the target asynchronous function with Redis caching.
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_builder(*args, **kwargs)
            cached_data = await redis_client.get(key)

            if cached_data:
                return pickle.loads(cached_data)

            result = await func(*args, **kwargs)

            if result:
                await redis_client.set(key, pickle.dumps(result), ex=expire)

            return result

        return wrapper

    return decorator
