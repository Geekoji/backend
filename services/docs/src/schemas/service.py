from typing import Any

from pydantic import BaseModel, field_validator

__all__ = ["Service"]


class Service(BaseModel):
    name: str

    @property
    def title(self) -> str:
        return f"{self.name.title()} Service"

    @property
    def openapi_url(self) -> str:
        return f"/openapi/{self.name}-service.json"

    @property
    def swagger_data(self) -> dict[str, Any]:
        return {"name": self.title, "url": self.openapi_url}

    # noinspection PyMethodParameters
    @field_validator("name", mode="after")
    def validate_name(cls, value: str) -> str:
        return value.lower()
