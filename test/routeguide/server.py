import asyncio
import contextlib
import logging
import os.path
import tempfile
import test.lib.routeguide as lib
from typing import Any, AsyncIterator

from grpclib.server import Server
from grpclib.utils import graceful_exit

from protoflux.servicer import grpc_method, grpc_name, grpc_service

logging.getLogger(__name__)

SERVER_START = "SERVING"
SOCKET_FILENAME = "routeguide"


@grpc_service("routeguide.RouteGuide")
class RouteGuide:
    def __init__(self, offset: int) -> None:
        self.offset = offset

    @grpc_method
    async def get_feature(self, request: lib.Point) -> lib.Feature:
        return lib.Feature(
            "Test", lib.Point(request.latitude + self.offset, request.longitude + self.offset)
        )

    @grpc_method
    @grpc_name("ListFeatures")
    async def list_f(self, request: lib.Rectangle) -> AsyncIterator[lib.Feature]:
        for lat in range(request.lo.latitude, request.hi.latitude):
            yield lib.Feature(
                "Test2", lib.Point(lat + self.offset, request.lo.longitude + self.offset)
            )


@contextlib.asynccontextmanager
async def start_server(socket_path: str, *args: Any, **kwargs: Any):
    server = Server([RouteGuide(*args, **kwargs)])
    await server.start(path=socket_path)
    logging.info(SERVER_START)
    logging.info(socket_path)
    yield server


async def main():
    server = Server([RouteGuide()])

    with graceful_exit([server]):
        with tempfile.TemporaryDirectory() as tf:
            socket_path = os.path.join(tf, SOCKET_FILENAME)
            await server.start(path=socket_path)
            print(SERVER_START)
            print(socket_path)
            await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
