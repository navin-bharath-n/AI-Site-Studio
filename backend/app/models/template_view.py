"""
TemplateAccountView ORM model — tracks unique account views per template.
Ensures an account viewing a template multiple times only counts as 1 view.
"""

import uuid
from sqlalchemy import ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class TemplateAccountView(UUIDMixin, TimestampMixin, Base):
    """Tracks unique account views for a template (1 view recorded per account)."""

    __tablename__ = "template_account_views"
    __table_args__ = (
        UniqueConstraint("user_id", "template_id", name="uq_template_account_view"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    template = relationship("Template", foreign_keys=[template_id])

    def __repr__(self) -> str:
        return f"<TemplateAccountView user={self.user_id} template={self.template_id}>"
