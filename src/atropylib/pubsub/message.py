import base64
import json
from datetime import datetime
from typing import Any

from nats.aio.msg import Msg
from pydantic import BaseModel


class Message(BaseModel):
    class Config:
        frozen = True

    source: str
    uuid: str
    time: datetime
    payload: dict[str, Any]
    extra_metadata: dict[str, str]
    subject: str | None = None

    def to_nats_msg(self) -> bytes:
        """
        Convert the message to a NATS message.
        """
        # Base64 encode the payload
        payload = base64.b64encode(json.dumps(self.payload).encode()).decode()
        metadata = {
            "source": self.source,
            "uuid": self.uuid,
            "time": self.time.isoformat(),
            **self.extra_metadata,
        }
        if self.subject:
            metadata["subject"] = self.subject
        uuid = self.uuid

        return json.dumps({"Metadata": metadata, "Payload": payload, "UUID": uuid}).encode("utf-8")

    @staticmethod
    def from_nats_msg(msg: Msg) -> "Message":
        """
        Convert a NATS message to a Message object.
        """
        data = msg.data.decode("utf-8")
        json_data: dict[str, Any] = json.loads(data)  # type: ignore[assignment]
        payload: dict[str, Any] = json.loads(base64.b64decode(json_data["Payload"]).decode())  # type: ignore[assignment]
        uuid: str = json_data["UUID"]
        msg_metadata: dict[str, str] = json_data["Metadata"]

        time = datetime.fromisoformat(msg_metadata["time"])
        source = msg_metadata["source"]
        subject = msg_metadata.get("subject", None)
        extra_metadata = {
            k: v
            for k, v in msg_metadata.items()
            if k
            not in [
                "source",
                "time",
                "subject",
            ]
        }

        return Message(
            source=source,
            uuid=uuid,
            time=time,
            payload=payload,
            extra_metadata=extra_metadata,
            subject=subject,
        )
