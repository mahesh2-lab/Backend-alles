import importlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.init_db import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    candidate_profile_id = Column(
        String,
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )
    requisition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisitions.id"),
        nullable=True,
    )
    evaluation_id = Column(
        String,
        ForeignKey("evaluations.id"),
        nullable=True,
    )

    room_name = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    candidateDetails = relationship(
        lambda: importlib.import_module(
            "src.models.candidateprofile").CandidateProfile,
        back_populates="interviews",
    )

    requisition = relationship(
        lambda: importlib.import_module("src.models.Requisition").Requisition,
        back_populates="interviews",
    )

    evaluationResult = relationship(
        lambda: importlib.import_module("src.models.evaluations").Evaluation,
        back_populates="interview",
        uselist=False,
    )
