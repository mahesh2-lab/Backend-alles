
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ExperienceItem(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None  # e.g., "Jan 2022 - Present"


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None

    @field_validator("graduation_year", mode="before")
    @classmethod
    def coerce_graduation_year(cls, v):
        # Accept ints or strings, normalize to string
        if v is None:
            return v
        return str(v).strip()


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    experienceMonths: Optional[int] = Field(
        None, description="Total computed experience in months")
    education: Optional[List[EducationItem]] = None

    @field_validator("experienceMonths", mode="before")
    @classmethod
    def coerce_experience_months(cls, v):
        if v is None:
            return v
        try:
            if isinstance(v, str):
                return int(v.strip())
            return int(v)
        except Exception:
            return v


class ScoreBreakdown(BaseModel):
    skills_match: Optional[float] = Field(None, description="Score out of 50")
    experience_match: Optional[float] = Field(
        None, description="Score out of 30")
    education_match: Optional[float] = Field(
        None, description="Score out of 20")

    @field_validator("skills_match", "experience_match", "education_match", mode="before")
    @classmethod
    def coerce_float_fields(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except Exception:
            return v


class MatchAnalysis(BaseModel):
    summary: Optional[str] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None


class Evaluation(BaseModel):
    match_score: Optional[float] = Field(None, ge=0, le=100)
    is_eligible: Optional[bool] = None
    match_analysis: Optional[MatchAnalysis] = None

    @field_validator("match_score", mode="before")
    @classmethod
    def coerce_match_score(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except Exception:
            return v


class EvaluationOut(BaseModel):
    candidate_profile: Optional[CandidateProfile] = None
    evaluation: Optional[Evaluation] = None

    class Config:
        from_attributes = True


class EvaluationSingle(BaseModel):
    # Candidate profile fields (flattened)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    experienceMonths: Optional[int] = Field(
        None, description="Total computed experience in months")
    education: Optional[List[EducationItem]] = None

    # Evaluation fields (flattened)
    match_score: Optional[float] = Field(None, ge=0, le=100)
    match_analysis: Optional[MatchAnalysis] = None
    is_eligible: Optional[bool] = None

    class Config:
        from_attributes = True
