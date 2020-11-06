def main():
    """Outputs lots of metadata to demonstatre the inner workings."""
    from typing import AsyncIterable, AsyncIterator

    import betterproto
    import grpclib.server

    from protoflux.servicer import Servicer, grpc_method, grpc_name, grpc_service

    class Req(betterproto.Message):
        pass

    class Res(betterproto.Message):
        pass

    @grpc_name(rpc_name="stubbed-service.Service")
    class StubbedService(Servicer):
        def __init__(self, rank: int, name: str) -> None:
            self.rank = rank
            self.name = name

        @grpc_method
        async def one(self, request: Req) -> Res:
            return Res()

        @grpc_method
        async def two_for_one(self, request: Req) -> AsyncIterator[Res]:
            yield Res()

        @grpc_name("FiveSix")
        @grpc_method
        async def three(self, request: AsyncIterable[Req]) -> AsyncIterator[Res]:
            async for _ in request:
                yield Res()

    @grpc_service("decorated-service.Service")
    class DecoratedService:
        def __init__(self, rank: int, name: str) -> None:
            self.rank = rank
            self.name = name

        @grpc_method
        async def one(self, request: Req) -> Res:
            return Res()

        @grpc_method
        async def two_for_one(self, request: Req) -> AsyncIterator[Res]:
            yield Res()

        @grpc_method
        @grpc_name("FiveSix")
        async def three(self, request: AsyncIterable[Req]) -> AsyncIterator[Res]:
            async for _ in request:
                yield Res()

    stds = StubbedService(1, "foo")
    decs = DecoratedService(0, "bar")

    server = grpclib.server.Server([stds, decs])

    from pprint import pprint

    print()
    print(stds.rank, stds.name)
    print(decs.rank, decs.name)  # type:ignore # will not type-check
    print()

    print(stds.one)
    pprint(stds.one.__dict__)
    print()
    print(stds.two_for_one)
    pprint(stds.two_for_one.__dict__)
    print()
    print(stds.three)
    pprint(stds.three.__dict__)
    print()
    print(stds.__mapping__)
    pprint(stds.__mapping__())

    print()
    print(decs.one)  # type:ignore # will not type-check
    pprint(decs.one.__dict__)  # type:ignore # will not type-check
    print()
    print(decs.two_for_one)  # type:ignore # will not type-check
    pprint(decs.two_for_one.__dict__)  # type:ignore # will not type-check
    print()
    print(decs.three)  # type:ignore # will not type-check
    pprint(decs.three.__dict__)  # type:ignore # will not type-check
    print()
    print(decs.__mapping__)
    pprint(decs.__mapping__())

    print()
    pprint(server._mapping)  # type:ignore


if __name__ == "__main__":
    main()
