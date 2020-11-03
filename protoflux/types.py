from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, TypeVar, Union

import betterproto

_S = TypeVar("_S")
T = TypeVar("T", bound=betterproto.Message)
U = TypeVar("U", bound=betterproto.Message)

UnaryUnaryHandler = Callable[[_S, T], Awaitable[U]]
UnaryStreamHandler = Callable[[_S, T], AsyncIterator[U]]
StreamUnaryHandler = Callable[[_S, AsyncIterable[T]], Awaitable[U]]
StreamStreamHandler = Callable[[_S, AsyncIterable[T]], AsyncIterator[U]]

AnyHandler = Union[UnaryUnaryHandler, UnaryStreamHandler, StreamUnaryHandler, StreamStreamHandler]
