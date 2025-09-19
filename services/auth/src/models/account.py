import uuid
from typing import TYPE_CHECKING, Optional

from pydantic import EmailStr
from sqlalchemy import UUID, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from models import TimestampModel

if TYPE_CHECKING:  # pragma: no cover
    from models import OAuth2Account

__all__ = [
    "Account",
]


class Account(TimestampModel):

    id: Mapped[uuid.UUID] = mapped_column(  # noqa: VNE003
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    email: Mapped[EmailStr] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    oauth2: Mapped[Optional["OAuth2Account"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="joined",
    )
