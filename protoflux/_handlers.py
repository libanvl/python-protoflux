import collections.abc
from typing import (
    Any,
    AsyncIterable,
    Awaitable,
    Callable,
    Dict,
    Generic,
    NamedTuple,
    Tuple,
    Type,
    TypeVar,
    cast,
    get_origin,
    get_type_hints,
)

import betterproto
import grpclib.server
from grpclib.const import Cardinality

from protoflux.types import (
    AnyHandler,
    StreamStreamHandler,
    StreamUnaryHandler,
    T,
    U,
    UnaryStreamHandler,
    UnaryUnaryHandler,
)

_S = TypeVar("_S")

_RPCCallable = Callable[[_S, grpclib.server.Stream[T, U]], Awaitable[None]]

_cardinality_map: Dict[Tuple[bool, bool], Cardinality] = {
    (True, True): Cardinality.STREAM_STREAM,
    (True, False): Cardinality.STREAM_UNARY,
    (False, True): Cardinality.UNARY_STREAM,
    (False, False): Cardinality.UNARY_UNARY,
}


def _get_cardinality_key(request_t: Type[Any], response_t: Type[Any]) -> Tuple[bool, bool]:
    return (
        get_origin(request_t) is collections.abc.AsyncIterable,  # type: ignore
        get_origin(response_t) is collections.abc.AsyncIterator,  # type: ignore
    )


def _unary_unary_factory(func: UnaryUnaryHandler[_S, T, U]) -> _RPCCallable[_S, T, U]:
    async def _inner(self: _S, stream: grpclib.server.Stream[T, U]):
        request = await stream.recv_message()
        assert isinstance(request, betterproto.Message)
        response = await func(self, request)
        await stream.send_message(response)

    return _inner


def _unary_stream_factory(func: UnaryStreamHandler[_S, T, U]) -> _RPCCallable[_S, T, U]:
    async def _inner(self: _S, stream: grpclib.server.Stream[T, U]):
        request = await stream.recv_message()
        assert isinstance(request, betterproto.Message)
        response_iter = func(self, request)

        if isinstance(response_iter, collections.abc.AsyncIterator):  # type:ignore
            async for response in response_iter:
                await stream.send_message(response)
        else:
            response_iter.close()  # type: ignore

    return _inner


def _stream_unary_factory(func: StreamUnaryHandler[_S, T, U]) -> _RPCCallable[_S, T, U]:
    async def _inner(self: _S, stream: grpclib.server.Stream[T, U]):
        async def _request_iterator() -> AsyncIterable[T]:
            async for request in stream:
                yield request

        request_iter = _request_iterator()
        response = await func(self, request_iter)
        await stream.send_message(response)

    return _inner


def _stream_stream_factory(func: StreamStreamHandler[_S, T, U]) -> _RPCCallable[_S, T, U]:
    async def _inner(self: _S, stream: grpclib.server.Stream[T, U]):
        async def _request_iterator() -> AsyncIterable[T]:
            async for request in stream:
                yield request

        request_iter = _request_iterator()
        response_iter = func(self, request_iter)

        if isinstance(response_iter, collections.abc.AsyncIterator):  # type: ignore
            async for response in response_iter:
                await stream.send_message(response)
        else:
            response_iter.close()  # type: ignore

    return _inner


class _RPCInfo(NamedTuple, Generic[_S, T, U]):
    cardinality: Cardinality
    request_t: Type[T]
    response_t: Type[U]
    handler: _RPCCallable[_S, T, U]


def get_rpc_info(handler: AnyHandler[_S, T, U]) -> "_RPCInfo[_S, T, U]":
    request_t, response_t = list(get_type_hints(handler).values())
    cardinality = _cardinality_map[_get_cardinality_key(request_t, response_t)]

    if cardinality == Cardinality.UNARY_UNARY:
        return _RPCInfo(
            cardinality,
            request_t,
            response_t,
            _unary_unary_factory(cast(UnaryUnaryHandler[_S, T, U], handler)),
        )
    elif cardinality == Cardinality.UNARY_STREAM:
        return _RPCInfo(
            cardinality,
            request_t,
            response_t,
            _unary_stream_factory(cast(UnaryStreamHandler[_S, T, U], handler)),
        )
    elif cardinality == Cardinality.STREAM_UNARY:
        return _RPCInfo(
            cardinality,
            request_t,
            response_t,
            _stream_unary_factory(cast(StreamUnaryHandler[_S, T, U], handler)),
        )
    elif cardinality == Cardinality.STREAM_STREAM:
        return _RPCInfo(
            cardinality,
            request_t,
            response_t,
            _stream_stream_factory(cast(StreamStreamHandler[_S, T, U], handler)),
        )

    raise ValueError(handler, cardinality)
