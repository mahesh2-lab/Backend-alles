from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text, ARRAY
from sqlalchemy.orm import relationship
import importlib
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from datetime import datetime
from uuid import uuid4
from src.db.init_db import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()::text"),
        nullable=False,
    )

    name = Column(String, nullable=False)
    email = Column(String, unique=False, index=True, nullable=False)
    phone = Column(String, nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    experience = Column(JSONB, nullable=True)
    experience_months = Column(Integer, nullable=True)
    education = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    evaluated_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    evaluated_by = relationship(
        lambda: importlib.import_module("src.models.user").User,
        back_populates="candidate_profiles",
    )

    evaluation = relationship(
        lambda: importlib.import_module("src.models.evaluations").Evaluation,
        back_populates="candidate",
        uselist=False,
    )

    interviews = relationship(
        lambda: importlib.import_module("src.models.interview").Interview,
        back_populates="candidateDetails",
        cascade="all, delete-orphan",
    )
