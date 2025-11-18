from fastapi import APIRouter, Depends, Form, HTTPException, Request, status, Response, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Any, List, Optional, cast
from datetime import datetime, date, time
from sqlalchemy.orm import joinedload
from src.schemas.evaluation import EvaluationSingle
from sqlalchemy.inspection import inspect
from sqlalchemy import or_
    

from src.services.process_evalution import event_stream_generator
from ..deps import get_current_active_user
from src.models.candidateprofile import CandidateProfile
from src.schemas.candidateSchema import CandidateCreate, CandidateResponse
from src.models.evaluations import Evaluation as EvalModel

from src.models.Requisition import Requisition
from src.db.init_db import get_db
from sqlalchemy.exc import IntegrityError
import re

router = APIRouter()


def serialize_instance(obj, visited=None):
    """Recursively serialize a SQLAlchemy model instance (including relationships).

    - Prevents infinite recursion by tracking visited primary-key identities.
    - Returns plain Python types suitable for JSON response.
    """
    if obj is None:
        return None

    if visited is None:
        visited = set()

    try:
        insp = inspect(obj)
    except Exception:
        # Not a SQLAlchemy object; return as-is if it's a primitive or mapping
        return obj

    # Build identity tuple (class name + primary key values) to avoid cycles
    pk_vals = tuple(getattr(obj, pk.name) for pk in insp.mapper.primary_key)
    identity = (obj.__class__.__name__, pk_vals)
    if identity in visited:
        # Already serialized this instance higher in the tree -> avoid loop.
        # Instead of returning None (which loses information), return a
        # lightweight reference object containing the class name and primary
        # key(s). This keeps the payload informative while preventing
        # infinite recursion.
        if len(pk_vals) == 1:
            pk_val = pk_vals[0]
        else:
            pk_val = list(pk_vals)
        return {"__ref__": obj.__class__.__name__, "pk": pk_val}
    visited.add(identity)

    data = {}
    # serialize columns
    for col in insp.mapper.columns:
        try:
            data[col.key] = getattr(obj, col.key)
        except Exception:
            data[col.key] = None

    # serialize relationships
    for rel in insp.mapper.relationships:
        name = rel.key
        try:
            value = getattr(obj, name)
        except Exception:
            data[name] = None
            continue

        if value is None:
            data[name] = None
        elif rel.uselist:
            data[name] = [serialize_instance(item, visited) for item in value]
        else:
            data[name] = serialize_instance(value, visited)

    return data


@router.post("/new_evaluation")
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    requisition: str = Form(None),
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint to process multiple uploaded files
    """
    if not files or len(files) == 0:
        return {"error": "No files uploaded"}

    if requisition is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requisition ID is required."
        )

    # Use sample job description if none provided
    job_desc = db.query(Requisition).filter(
        Requisition.id == requisition).first() if requisition else None

    if job_desc:
        job_description = cast(str, job_desc.requisition) + \
            "\n" + cast(str, job_desc.description)
    else:
        job_description = "Sample job description: Looking for a skilled software developer with experience in Python and FastAPI."

    return StreamingResponse(
        event_stream_generator(files, job_description,
                               request, current_user.id, requisition),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/evaluations", status_code=status.HTTP_200_OK)
def list_evaluations(
    skip: int = 0,
    limit: int = 100,
    today: bool = False,
    search: str = "",
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List candidate evaluations for requisitions created by the current user.
    
    - skip: number of items to skip (>= 0)
    - limit: max items to return (1..1000)
    - today: filter evaluations from today only
    - search: search by candidate name, email, or requisition title
    """
    # Validation
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="skip must be >= 0"
        )
    
    max_limit = 1000
    if limit < 1 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"limit must be between 1 and {max_limit}"
        )
    
    try:
        # Build the main query with eager loading
        # Filter evaluations for requisitions created by current user
        query = db.query(EvalModel).options(
            joinedload(EvalModel.candidate),
            joinedload(EvalModel.requisition_obj).joinedload(Requisition.creator)
        ).join(
            Requisition,
            EvalModel.requisition_id == Requisition.id
        ).join(
            CandidateProfile,
            EvalModel.candidate_id == CandidateProfile.id
        ).filter(
            Requisition.created_by == current_user.id
        )
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    CandidateProfile.name.ilike(search_term),
                    CandidateProfile.email.ilike(search_term),
                    Requisition.requisition.ilike(search_term)
                )
            )
        
        # Apply date filter if today flag is set
        if today:
            today_date = date.today()
            start_dt = datetime.combine(today_date, time.min)
            end_dt = datetime.combine(today_date, time.max)
            query = query.filter(
                EvalModel.evaluated_at >= start_dt,
                EvalModel.evaluated_at <= end_dt
            )
        
        # Execute query with pagination
        evaluations = query.offset(skip).limit(limit).all()
        
        # Serialize the results
        result = []
        for evaluation in evaluations:
            eval_dict = {
                "id": str(evaluation.id),
                "candidate_id": str(evaluation.candidate_id),
                "candidate_status": evaluation.candidate_status,
                "requisition_id": str(evaluation.requisition_id) if evaluation.requisition_id else None, # type: ignore
                "match_score": evaluation.match_score,
                "summary": evaluation.summary,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "report": evaluation.report,
                "interview_status": evaluation.interview_status,
                "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None, # type: ignore
            }
            
            # Add candidate data
            if evaluation.candidate:
                candidate = evaluation.candidate
                eval_dict["candidate"] = {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "skills": candidate.skills,
                    "experience": candidate.experience,
                    "experience_months": candidate.experience_months,
                    "education": candidate.education,
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                    "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
                    "evaluated_by_id": str(candidate.evaluated_by_id) if candidate.evaluated_by_id else None,
                    "evaluation": {
                        "__ref__": "Evaluation",
                        "pk": str(evaluation.id)
                    }
                }
            
            # Add requisition data
            if evaluation.requisition_obj:
                requisition = evaluation.requisition_obj
                req_dict = {
                    "id": str(requisition.id),
                    "requisition": requisition.requisition,
                    "description": requisition.description,
                    "created_by": str(requisition.created_by),
                    "created_at": requisition.created_at.isoformat() if requisition.created_at else None,
                    "updated_at": requisition.updated_at.isoformat() if requisition.updated_at else None,
                }
                
                # Add creator data if available
                if requisition.creator:
                    creator = requisition.creator
                    req_dict["creator"] = {
                        "__ref__": "User",
                        "pk": str(creator.id)
                    }
                
                eval_dict["requisition_obj"] = req_dict
            
            result.append(eval_dict)
        
        return result
        
    except Exception as e:
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch evaluations: {str(e)}"
        )