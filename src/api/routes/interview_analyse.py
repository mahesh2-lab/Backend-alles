import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from ..deps import get_current_active_user
from src.services.websocket import manager
from src.models.interview import Interview
from src.models.evaluations import Evaluation
from src.db.init_db import get_db
from src.services.livekit import verify_livekit_token
from pydantic import BaseModel
from src.services.process_interview import analyze_transcript_content


class PasswordCheckRequest(BaseModel):
    id: str
    password: str


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_data(payload: dict, db: Session = Depends(get_db)):

    transcript_data = payload.get("transcript_data")
    room_name = payload.get("room_name")
    candidate_details = payload.get("candidate_details")
    job_description = payload.get("job_description")

    processed = {
        "transcript_data": transcript_data,
        "room_name": room_name,
        "candidate_details": candidate_details,
        "job_description": job_description,
    }

    if transcript_data and room_name:
        analysis_result = analyze_transcript_content(transcript_data)

        if "error" in analysis_result:
            raise HTTPException(
                status_code=500, detail=analysis_result["error"])

        interview = (
            db.query(Interview)
            .options(joinedload(Interview.evaluationResult))
            .filter(Interview.room_name == room_name)
            .first()
        )
        if not interview:
            raise HTTPException(
                status_code=404, detail="Interview not found for provided room name")

        evaluation = interview.evaluationResult
        if not evaluation:
            raise HTTPException(
                status_code=404, detail="Evaluation not linked to interview")

        report_payload = analysis_result.get("analysis") or analysis_result
        evaluation.report = report_payload
        evaluation.interview_status = True

        try:
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to persist interview analysis for room %s", room_name)
            raise HTTPException(
                status_code=500, detail="Failed to persist interview analysis")

    payload = {
        "status": "success",
        "room_name": room_name,
        "analysis": analysis_result,
    }

    await manager.broadcast(payload)

    return payload


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(ws)


@router.get('/get-context/{room_name}')
def get_context(room_name: str, db: Session = Depends(get_db)):
    interview = (
        db.query(Interview)
        .options(
            joinedload(Interview.candidateDetails),
            joinedload(Interview.requisition),
        )
        .filter(Interview.room_name == room_name)
        .first()
    )
    if not interview:
        raise HTTPException(
            status_code=404, detail="Interview context not found")

    candidate_payload = (
        jsonable_encoder(
            interview.candidateDetails,
            exclude={"evaluation", "interviews", "evaluated_by"},
        )
        if getattr(interview, "candidateDetails", None)
        else None
    )

    requisition_payload = None
    job_description_text = ""
    if getattr(interview, "requisition", None):
        requisition_obj = interview.requisition
        requisition_payload = jsonable_encoder(
            requisition_obj,
            exclude={"evaluations", "interviews", "creator"},
        )
        title = requisition_obj.requisition or ""
        description = requisition_obj.description or ""
        job_description_text = (title + "\n" + description).strip()

    response_data = {
        "candidate_details": candidate_payload,
        "job_description": job_description_text,
    }

    return {"status": "success", "data": response_data}


@router.get('/get-data/{id}')
def get_data(id: str, db: Session = Depends(get_db)):
    try:
        if not id:
            raise HTTPException(
                status_code=400, detail="Room name is required")

        interview = (
            db.query(Interview)
            .options(
                joinedload(Interview.candidateDetails),
                joinedload(Interview.requisition),
                joinedload(Interview.evaluationResult),
            )
            .filter(Interview.id == id)
            .first()
        )
        if not interview:
            raise HTTPException(status_code=404, detail="Data not found")

        token_value = getattr(interview, "token", None)
        if token_value is not None and not isinstance(token_value, str):
            token_value = str(token_value)

        response = verify_livekit_token(token_value or "")
        valid = False
        if isinstance(response, dict):
            valid = response.get("valid", False)
        else:
            valid = getattr(response, "valid", False)

        if not valid:
            logger.warning(
                "LiveKit token validation failed for interview %s", interview.id)
            raise HTTPException(status_code=401, detail="Invalid token")

        base_payload = jsonable_encoder(
            interview,
            exclude={"candidateDetails", "requisition", "evaluationResult"},
        )

        candidate_payload = (
            jsonable_encoder(
                interview.candidateDetails,
                exclude={"evaluation", "interviews", "evaluated_by"},
            )
            if getattr(interview, "candidateDetails", None)
            else None
        )

        requisition_payload = (
            jsonable_encoder(
                interview.requisition,
                exclude={"evaluations", "interviews", "creator"},
            )
            if getattr(interview, "requisition", None)
            else None
        )

        evaluation_payload = (
            jsonable_encoder(
                interview.evaluationResult,
                exclude={"candidate", "requisition_obj", "interview"},
            )
            if getattr(interview, "evaluationResult", None)
            else None
        )
        interview_payload = (
            jsonable_encoder(
                interview,
                exclude={"candidateDetails",
                         "requisition", "evaluationResult"},
            )
        )

        base_payload.update(
            {

                "candidate": candidate_payload,
                "requisition": requisition_payload,
                "evaluation": evaluation_payload,
            }
        )

        return {"success": True, "data": base_payload}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch interview %s", id)
        raise HTTPException(
            status_code=500, detail="Internal server error") from exc


@router.post('/check-password')
def check_password(payload: PasswordCheckRequest, db: Session = Depends(get_db)):
    try:
        if not payload.id:
            raise HTTPException(status_code=400, detail="ID is required")
        if not payload.password:
            raise HTTPException(status_code=400, detail="Password is required")

        interview = db.query(Interview).filter(
            Interview.id == payload.id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Data not found")

        match = db.query(Interview).filter(
            Interview.id == payload.id,
            Interview.password == payload.password
        ).first()
        if not match:
            return {"success": False, "message": "Incorrect password"}

        return {"success": True, "message": "Password is correct"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get('/get-interviews')
def get_interviews(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    try:

        interviews = (
            db.query(Interview)
            .options(
                joinedload(Interview.candidateDetails),
                joinedload(Interview.evaluationResult),
                joinedload(Interview.requisition),
            )
            .join(Interview.evaluationResult)
            .join(Interview.requisition)
            .filter(
                Evaluation.interview_status == True,
                Evaluation.candidate_id.isnot(None),
                Interview.requisition.has(created_by=current_user.id),
            )
            .all()
        )

        results = []
        for interview in interviews:
            candidate_payload = (
                jsonable_encoder(
                    interview.candidateDetails,
                    exclude={"evaluation", "interviews", "evaluated_by"},
                )
                if getattr(interview, "candidateDetails", None)
                else None
            )
            evaluation_payload = (
                jsonable_encoder(
                    interview.evaluationResult,
                    exclude={"candidate", "requisition_obj", "interview"},
                )
                if getattr(interview, "evaluationResult", None)
                else None
            )
            requisition_payload = (
                jsonable_encoder(
                    interview.requisition,
                    exclude={"evaluations", "interviews", "creator"},
                )
                if getattr(interview, "requisition", None)
                else None
            )
            interview_payload = jsonable_encoder(
                interview,
                exclude={"candidateDetails",
                         "requisition", "evaluationResult"},
            )
            interview_payload.update(
                {
                    "candidate": candidate_payload,
                    "evaluation": evaluation_payload,
                    "requisition": requisition_payload,
                }
            )
            results.append(interview_payload)

        return {"success": True, "data": results}

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get('/get-interview/{interview_id}')
def get_interview_by_id(interview_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    try:
        interview = (
            db.query(Interview)
            .options(
                joinedload(Interview.candidateDetails),
                joinedload(Interview.evaluationResult),
                joinedload(Interview.requisition),
            )
            .filter(
                Interview.id == interview_id,
                Interview.requisition.has(created_by=current_user.id),
            )
            .first()
        )

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        if not interview.evaluationResult or not interview.evaluationResult.interview_status or not interview.evaluationResult.candidate_id:
            raise HTTPException(
                status_code=404, detail="Interview not completed or evaluation missing")

        candidate_payload = (
            jsonable_encoder(
                interview.candidateDetails,
                exclude={"evaluation", "interviews", "evaluated_by"},
            )
            if getattr(interview, "candidateDetails", None)
            else None
        )
        evaluation_payload = (
            jsonable_encoder(
                interview.evaluationResult,
                exclude={"candidate", "requisition_obj", "interview"},
            )
            if getattr(interview, "evaluationResult", None)
            else None
        )
        requisition_payload = (
            jsonable_encoder(
                interview.requisition,
                exclude={"evaluations", "interviews", "creator"},
            )
            if getattr(interview, "requisition", None)
            else None
        )

        interview_payload = jsonable_encoder(
            interview,
            exclude={"candidateDetails", "requisition", "evaluationResult"},
        )
        interview_payload.update(
            {
                "candidate": candidate_payload,
                "evaluation": evaluation_payload,
                "requisition": requisition_payload,
            }
        )

        return {"success": True, "data": interview_payload}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
