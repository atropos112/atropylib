"""
Example usage

async def main():
    # Example usage
    nats_client = NATSClient()

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

    async def publish(self, subject: str, message: Message, create_stream_if_not_exist: bool = True) -> None:
        """
        Publish a message to a subject in NATS JetStream.

        If `create_stream_if_not_exist` is True, it will create the stream if it does not exist. This causes a
        performance hit of ~1ms on the first publish only.
        """
        if create_stream_if_not_exist and subject not in self._added_streams:
            # INFO: The stream may not exist. We try to create it by calling add_stream. This is only really
            # needed on the first publish. After that, we can assume the stream exists.
            # The cost of that is approximately 1ms, and that is only on the first publish.
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
        deliver_policy: DeliverPolicy | None = None,
    ) -> AsyncGenerator[Message, Any]:
        """
        Subscribe to a subject in NATS JetStream and yield messages.

        If you want
        - all messages, set `deliver_policy` to DeliverPolicy.ALL.
        - new messages only, set `deliver_policy` to DeliverPolicy.NEW.
        - messages starting from a specific time, set `deliver_policy` to
          DeliverPolicy.BY_START_TIME and `start_time` to the desired start time.

        Coundn't get BY_START_TIME to work. If set timestamp must be provided in the
        ConsumerConfig, but when provided it outputs an error:
        "invalid JSON: Time.UnmarshalJSON: input is not a JSON string"
        """
        global _SVC_NAME

        consumer_config = ConsumerConfig(
            ack_policy=AckPolicy.EXPLICIT,
            flow_control=True,
            durable_name=_SVC_NAME,
            idle_heartbeat=30,
        )

        sub = await self._js.subscribe(
            subject=subject,
            durable=_SVC_NAME,
            config=consumer_config,
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
