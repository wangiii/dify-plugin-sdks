from collections.abc import Callable
from functools import wraps
import inspect
from typing import Any

from dify_plugin.core.runtime.session import Session

class Route:
    filter: Callable[[dict], bool]
    func: Callable

    def __init__(self, filter: Callable[[dict], bool], func) -> None:
        self.filter = filter
        self.func = func

class Router:
    routes: list[Route]

    def __init__(self) -> None:
        self.routes = []

    def register_route(self, f: Callable, filter: Callable[[dict], bool], instance: Any = None):
        sig = inspect.signature(f)
        parameters = list(sig.parameters.values())
        if len(parameters) == 0:
            raise ValueError("Route function must have at least one parameter")
        
        if instance:
            # get first parameter of func
            parameter = parameters[2]
            # get annotation of the first parameter
            annotation = parameter.annotation
            def wrapper(session: Session, data: dict):
                try:
                    data = annotation(**data)
                except TypeError:
                    raise ValueError(f"Cannot parse data to {annotation}")
                return f(instance, session, data)
        else:
            # get first parameter of func
            parameter = parameters[1]
            # get annotation of the first parameter
            annotation = parameter.annotation
            def wrapper(session: Session, data: dict):
                try:
                    data = annotation(**data)
                except TypeError:
                    raise ValueError(f"Cannot parse data to {annotation}")
                return f(session, data)

        self.routes.append(Route(filter, wrapper))
    
    def dispatch(self, session: Session, data: dict) -> Any:
        for route in self.routes:
            if route.filter(data):
                return route.func(session, data)