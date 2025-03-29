import os

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from atropylib.errors import DeveloperError


def get_resource(service_name: str | None = None) -> Resource:
    service_name = service_name or os.getenv("ATRO_SERVICE_NAME", None)

    if not service_name:
        raise DeveloperError(
            "Service name must be provided either thorugh the function argument "
            "or the environment variable (ATRO_SERVICE_NAME)."
        )

    return Resource({SERVICE_NAME: service_name})
