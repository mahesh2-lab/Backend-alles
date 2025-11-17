from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
import importlib
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from src.db.init_db import Base


class Requisition(Base):
    __tablename__ = "requisitions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # identifier or title of the requisition
    requisition = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    evaluations = relationship(
        lambda: importlib.import_module("src.models.evaluations").Evaluation,
        back_populates="requisition_obj",
        cascade="all, delete-orphan",
    )

    interviews = relationship(
        lambda: importlib.import_module("src.models.interview").Interview,
        back_populates="requisition",
        cascade="all, delete-orphan",
    )

    creator = relationship(
        lambda: importlib.import_module("src.models.user").User,
        back_populates="requisitions",
        foreign_keys=[created_by],
    )
