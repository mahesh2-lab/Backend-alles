from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.orm import relationship
import importlib
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from src.db.init_db import Base
from uuid import uuid4


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    team_role = Column(String, default="hr", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    # Relationship
    requisitions = relationship(
        lambda: importlib.import_module("src.models.Requisition").Requisition,
        cascade="all, delete-orphan",
        back_populates="creator",
    )

    candidate_profiles = relationship(
        lambda: importlib.import_module(
            "src.models.candidateprofile").CandidateProfile,
        back_populates="evaluated_by",
        cascade="all, delete-orphan",
    )
