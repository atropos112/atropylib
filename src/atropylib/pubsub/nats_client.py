"""
Example usage

async def main():
    # Example usage
    nats_client = NATsClient()

    message = Message(
        source="example_source",
        uuid="example_uuid",
        time=datetime.now(),
        payload={"key": "value"},
        extra_metadata={"meta_key": "meta_value"},
        subject="test",
    )

    from time import time

    start = time()
    await nats_client.publish("test", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    start = time()
    await nats_client.publish("test", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    start = time()
    await nats_client.publish("test", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    start = time()
    await nats_client.publish("blah", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    start = time()
    await nats_client.publish("blah", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    start = time()
    await nats_client.publish("test", message)
    end = time()
    print(f"Published message in {end - start} seconds")

    print("Waiting for message...")
    counter = 0
    async for i in nats_client.subscribe("test"):
        print(i)
        counter += 1
        print(counter)


asyncio.run(main())
"""

import asyncio
import os
from functools import cached_property
from typing import Any, AsyncGenerator

from nats import connect
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import BaseModel, PrivateAttr

from atropylib.pubsub.message import Message

_SVC_NAME = os.getenv("ATRO_SVC_NAME", "")
_DEFAULT_CONSUMER_CONFIG = ConsumerConfig(
    ack_policy=AckPolicy.EXPLICIT,
    flow_control=True,
    durable_name=_SVC_NAME,
    idle_heartbeat=30,
)


async def get_nats_client(nats_url: str | None = None) -> NATS:
    """
    Connect to a NATS server and return the JetStream context.

    If `url` is not provided, we check the environment variable `ATRO_NATS_URL` for the server URL.
    """
    url = nats_url or os.getenv("ATRO_NATS_URL", None)

    if url is None:
        raise ValueError("NATs url is required but it was not provided and neither was env ATRO_NATS_URL.")

    # Connect to the NATS server
    nc = await connect(url)

    return nc


async def get_jetstream_client(nats_url: str | None = None) -> JetStreamContext:
    """
    Connect to a NATS server and return the JetStream context.

    If `url` is not provided, we check the environment variable `ATRO_NATS_URL` for the server URL.
    """
    nc = await get_nats_client(nats_url)

    return nc.jetstream()


class NATSClient(BaseModel):
    """
    A client for interacting with NATS JetStream.
    """

    nats_url: str | None = None
    _added_streams: set[str] = PrivateAttr(default_factory=set)

    @cached_property
    def _nc(self) -> NATS:
        """
        Return the NATS client.
        """
        import nest_asyncio

        nest_asyncio.apply()
        coro = get_nats_client(self.nats_url)
        nc = asyncio.run(coro)
        return nc

    @cached_property
    def _js(self) -> JetStreamContext:
        """
        Return the JetStream context.
        """
        return self._nc.jetstream()

    async def publish(self, subject: str, message: Message) -> None:
        """
        Publish a message to a subject.
        """
        if subject not in self._added_streams:
            await self._js.add_stream(name=subject, subjects=[subject])
            self._added_streams.add(subject)

        # Using jetstream publish is flaky so using nc.request directly.
        # Can use nc with request to impose a timeout but that is never been needed and imposes a huge
        # slow down so using .publish instaed with nats client.
        await self._nc.publish(
            subject=subject,
            payload=message.to_nats_msg(),
            headers=None,
        )

    async def subscribe(
        self,
        subject: str,
        deliver_policy: DeliverPolicy = DeliverPolicy.NEW,
    ) -> AsyncGenerator[Message, Any]:
        global _DEFAULT_CONSUMER_CONFIG, _SVC_NAME
        sub = await self._js.subscribe(
            subject=subject,
            durable=_SVC_NAME,
            config=_DEFAULT_CONSUMER_CONFIG,
            manual_ack=True,
            flow_control=True,
            deliver_policy=deliver_policy,
        )
        try:
            async for msg in sub.messages:
                # Order here matters, if we can't decode the message, we don't want to ack it
                message = Message.from_nats_msg(msg)
                await msg.ack()

                yield message
        finally:
            await sub.unsubscribe()
