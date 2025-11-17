from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text, ARRAY, Boolean
from sqlalchemy.orm import relationship
import importlib
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from uuid import uuid4
from enum import Enum
from src.db.init_db import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()::text"),
        nullable=False,
    )

    candidate_id = Column(String, ForeignKey(
        "candidate_profiles.id"), nullable=False)
    candidate_status = Column(Boolean, default=True, nullable=False)

    requisition_id = Column(
        UUID(as_uuid=True), ForeignKey("requisitions.id"), nullable=True
    )

    match_score = Column(Integer, nullable=True)
    summary = Column(String, nullable=True)

    strengths = Column(ARRAY(String), nullable=True)
    weaknesses = Column(ARRAY(String), nullable=True)

    interview_status = Column(Boolean, default=False, nullable=False)

    report = Column(
        JSONB,
        nullable=True
    )

    evaluated_at = Column(DateTime, default=datetime.now, nullable=False)

    candidate = relationship(
        lambda: importlib.import_module(
            "src.models.candidateprofile").CandidateProfile,
        back_populates="evaluation",
    )

    requisition_obj = relationship(
        lambda: importlib.import_module("src.models.Requisition").Requisition,
        back_populates="evaluations",
    )

    interview = relationship(
        lambda: importlib.import_module("src.models.interview").Interview,
        back_populates="evaluationResult",
        uselist=False,
    )
