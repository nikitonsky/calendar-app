import typing as tp
import functools
from starlette.routing import Route


ROUTE_TABLE = []


def route(path: str, method: tp.Optional[str] = None):
    def decorator(func, method=None):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            return await func(*args, **kwargs)
        if method is None:
            method = ['GET', 'POST']
        else:
            method = [method]
        ROUTE_TABLE.append(Route(path, wrapped, methods=method))

        return wrapped
    return decorator
