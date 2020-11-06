import logging
import os
import tempfile
import test.gen.routeguide as rg
import test.routeguide.server as rgserver
from typing import List

import pytest
from grpclib.client import Channel

logging.getLogger(__name__)

SOCKET_FILENAME = "routeguide"


@pytest.mark.asyncio
async def test_one():
    offset = 2
    with tempfile.TemporaryDirectory() as tf:
        socket_path = os.path.join(tf, SOCKET_FILENAME)

        async with rgserver.start_server(socket_path, offset=offset) as server:
            async with Channel(path=socket_path) as channel:
                client = rg.RouteGuideStub(channel)
                res = await client.get_feature(latitude=10, longitude=20)
                assert res.location.latitude == 10 + offset
                assert res.location.longitude == 20 + offset
                logging.info("get_feature")

                features: List[rg.Feature] = []
                async for f in client.list_features(lo=rg.Point(10, 20), hi=rg.Point(20, 20)):
                    features.append(f)

                assert len(features) == (20 - 10)
                assert features[0].location.latitude == 10 + offset
                logging.info("list_feature")

            logging.info("Closing")
            server.close()
