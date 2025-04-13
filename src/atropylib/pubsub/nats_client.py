"""
Example usage

async def main():
    init_logger_provider(level=logging.DEBUG)

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

    await nats_client.publish("test", message)
    await nats_client.publish("test", message)
    await nats_client.publish("test", message)
    await nats_client.publish("test", message)
    await nats_client.publish("test", message)

    async for msg in nats_client.subscribe(
        "test",
        DeliverPolicy.BY_START_TIME,
        timedelta(minutes=3),
    ):
        print(msg)


asyncio.run(main())
"""

import asyncio
import os
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any, AsyncGenerator

import pytz
from nats import connect
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import BaseModel, PrivateAttr

from atropylib.pubsub.message import Message
from atropylib.telemetry.logs import StructuredLogger

_SVC_NAME = os.getenv("ATRO_SVC_NAME", "")

UTC_TZ = pytz.utc


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
    _logger: StructuredLogger = PrivateAttr(default_factory=lambda: StructuredLogger("NATS_Client"))

    @cached_property
    def _nc(self) -> NATS:
        """
        Return the NATS client.
        """
        import nest_asyncio

        nest_asyncio.apply()
        if self.nats_url is None:
            self.nats_url = os.getenv("ATRO_NATS_URL", None)

        coro = get_nats_client(self.nats_url)
        nc = asyncio.run(coro)

        global _SVC_NAME
        self._logger = self._logger.bind(nats_url=self.nats_url, service_name=_SVC_NAME)
        self._logger.info("Connected to NATS server")
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
        self._logger.debug(
            "Publishing message to NATS",
            subject=subject,
            msg_id=message.uuid,
            msg_time=message.time.isoformat(),
            msg_source=message.source,
            msg_subject=message.subject,
        )

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
        start: timedelta | None = None,
    ) -> AsyncGenerator[Message, Any]:
        """
        Subscribe to a subject in NATS JetStream and yield messages.

        If you want
        - all messages, set `deliver_policy` to DeliverPolicy.ALL.
        - new messages only, set `deliver_policy` to DeliverPolicy.NEW.
        - messages starting from a specific time, provide a `start` timedelta (from now).
          Optionally you can set `deliver_policy` to DeliverPolicy.BY_START_TIME, although
          leaving it as None will work too (as providing a start time will set the deliver_policy to BY_START_TIME).
          Do note, providing a different deliver_policy will raise an error.
        """
        global _SVC_NAME

        if start is None:
            if deliver_policy is DeliverPolicy.BY_START_TIME:
                raise ValueError("BY_START_TIME requires a start time.")

            opt_start_time = None
        else:
            if deliver_policy and deliver_policy != DeliverPolicy.BY_START_TIME:
                raise ValueError(
                    "You've set a start time but not BY_START_TIME as the deliver_policy."
                    "Either leave delivery_policy as None or set it to BY_START_TIME if you want to use a start time."
                )

            opt_start_time_dt = datetime.now(tz=UTC_TZ) - start
            opt_start_time = opt_start_time_dt.isoformat()

        consumer_config = ConsumerConfig(
            ack_policy=AckPolicy.EXPLICIT,
            flow_control=True,
            durable_name=_SVC_NAME,
            idle_heartbeat=30,
            # The opt_start_time is said to be int | None, but it is actually a string
            opt_start_time=opt_start_time,  # type: ignore
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
