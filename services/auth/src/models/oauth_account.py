import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Account, TimestampModel

__all__ = [
    "OAuth2Account",
]


class OAuth2Account(TimestampModel):

    __tablename__ = "oauth_accounts"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False)

    account: Mapped[Account] = relationship(
        back_populates="oauth2",
        lazy="joined",
    )
