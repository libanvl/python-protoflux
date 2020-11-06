import functools
import inspect
from typing import Any, Callable, Protocol, Type, TypeVar, get_args

import grpclib

from protoflux._handlers import get_rpc_info
from protoflux.types import AnyHandler, T, U

_S = TypeVar("_S")
_V = TypeVar("_V")


def grpc_name(rpc_name: str) -> Callable[[_V], _V]:
    """Sets or overrides the __rpc_name__ attribute for a given object.

    Args:
        rpc_name: The rpc name to set

    Returns:
        Callable[[_V], _V]: The decorator function that sets the attribute
    """

    def _wrapper(obj: _V) -> _V:
        """Sets or override the __rpc_name__ attribute for the given object.

        Args:
            obj: The object

        Returns:
            _V: The object with the attribute set
        """
        obj.__rpc_name__ = rpc_name
        return obj

    return _wrapper


def grpc_method(func: AnyHandler[_S, T, U]) -> AnyHandler[_S, T, U]:
    """Wraps the function for use as a grpclib Handler.

    By default, the rpc name is the function name transformed to title case.
    Override the default rpc name using the @grpc_name decorator.

    The type hints for request and result are used to determine the cardinality.
    For a streaming client, the request type must be AsyncIterable[_T] (note the _able_)
    For a stream server, the response type must be AsyncIterator[_U] (note the _ator_)

    Args:
        func: The handler function

    Returns:
        AnyHandler[_S, T, U]: The wrapped handler function
    """
    cardinality, request_t, response_t, call = get_rpc_info(func)

    if hasattr(func, "__rpc_name__"):
        rpc_name = func.__rpc_name__
    else:
        rpc_name = func.__name__.replace("_", " ").title().replace(" ", "")

    func.__rpc_name__ = rpc_name
    func.__rpc_call__ = call
    func.__rpc_req_t__ = (
        request_t if not cardinality.client_streaming else get_args(request_t)[0]  # type:ignore
    )
    func.__rpc_res_t__ = (
        response_t if not cardinality.server_streaming else get_args(response_t)[0]  # type:ignore
    )
    func.__rpc_cardinality__ = cardinality

    return func


def _is_rpc_call(member: Any) -> bool:
    return callable(member) and hasattr(member, "__rpc_call__")


class Servicer(Protocol):
    """Protocol that defines a protoflux service.

    Provides a default implementation of the grcplib IServable interface.
    If using as a base class, you must also use the @grpc_name decorator to
    set the service's rpc name, or set the __rpc_name__ attribute directly.
    """

    __rpc_name__: str

    def __mapping__(self):
        return {
            f"/{self.__rpc_name__}/{method.__rpc_name__}": grpclib.const.Handler(
                functools.partial(method.__rpc_call__, self),
                method.__rpc_cardinality__,
                method.__rpc_req_t__,
                method.__rpc_res_t__,
            )
            for _, method in inspect.getmembers(self, _is_rpc_call)
        }


class _DecoratedServicer(Servicer, Protocol[_V]):
    """Opaque wrapper for a decorated service class.

    At runtime, this will be an instance of _V.

    Type-checkers will see this as _DecoratedServicer[_V].

    The attributes of the original service class are available at runtime,
    but will be hidden from static type-checkers.

    This protocol is just there to help the @grpc_service decorator
    play nicely with the type-checker.

    There is no reason to implement this Protocol directly. Probably.
    """

    def __call__(self, *_: Any, **__: Any) -> "_DecoratedServicer[_V]":
        """Simulates the __init__ method for static type-checkers."""


def grpc_service(service_name: str) -> Callable[[Type[_V]], "_DecoratedServicer[_V]"]:
    """Wraps the class for use as a grcplib IServable.

    Args:
        service_name: The rpc name of the service
    """

    def _wrapper(cls: Type[_V]) -> _DecoratedServicer[_V]:
        """Implements the Servicer Protocol on cls"""
        setattr(cls, "__mapping__", Servicer.__mapping__)
        setattr(cls, "__rpc_name__", service_name)
        return cls

    return _wrapper
