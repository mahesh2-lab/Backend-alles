from fastapi import Depends, FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from typing import Any, List, Optional
import asyncio
import json
from sqlalchemy.orm import Session
from datetime import datetime
import traceback
from .process_file import parse_resume
import tempfile
import os
import inspect
from ..models.candidateprofile import CandidateProfile
from ..models.evaluations import Evaluation
from ..db.init_db import get_db
from ..api.deps import get_current_active_user
from ..worker.conn import send_email_task
import uuid
from sqlalchemy.exc import IntegrityError


async def process_evaluation_job(
    file_path: str,
    job_description: str,
    current_user: Any = None,
    requisition: Any = None
):

    db = next(get_db())

    result_candidate = parse_resume(file_path, job_description)

    print("Parsed candidate data:", result_candidate)

    result = result_candidate.get("candidate_profile", {})
    eval_data = result_candidate.get("evaluation", {})
    
    
    new = CandidateProfile(
        name=result.get("name", "Unknown"),  # type: ignore
        email=result.get("email"),  # type: ignore
        phone=result.get("phone"),  # type: ignore
        skills=result.get("skills", []),  # type: ignore
        experience=result.get("experience", []),  # type: ignore
        experience_months=result.get("experienceMonths"),   # type: ignore
        education=result.get("education", []),  # type: ignore
        evaluated_by_id=current_user
    )

    db.add(new)
    db.commit()
    db.refresh(new)

    # defensively read nested fields
    match_analysis = eval_data.get("match_analysis") or {} # type: ignore 
    summary = match_analysis.get("summary") if isinstance(
        match_analysis, dict) else None
    strengths = match_analysis.get("strengths") if isinstance(
        match_analysis, dict) else None
    weaknesses = match_analysis.get("weaknesses") if isinstance(
        match_analysis, dict) else None

    # convert requisition to UUID if a string was provided
    requisition_id = None
    if requisition:
        try:
            requisition_id = uuid.UUID(str(requisition))
        except Exception:
            # leave as-is; DB driver may accept string UUIDs, but keep safe
            requisition_id = requisition

    # create evaluation using relationship so SQLAlchemy keeps both sides in sync
    new_eval = Evaluation(
        candidate=new,
        candidate_status=eval_data.get("is_eligible"),  # type: ignore
        match_score=eval_data.get("match_score"),  # type: ignore
        summary=summary,  # type: ignore
        strengths=strengths,  # type: ignore
        weaknesses=weaknesses,  # type: ignore
        requisition_id=requisition_id,
    )

    try:
        db.add(new_eval)
        db.commit()
        db.refresh(new_eval)
        # also refresh candidate so relationship is populated
        db.refresh(new)
    except IntegrityError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    position = (job_description or "").split('\n', 1)[0]

    task = send_email_task.delay(
        to_email=new.email,
        candidate_name=new.name,
        position=position,
        is_eligible=eval_data.get("is_eligible"), # type: ignore
        candidate_id=new.id,
        evaluation_id=new_eval.id,
        requisition_id=requisition_id
        
    )
    
    # send_email_task(
    #     to_email=new.email, # type: ignore
    #     candidate_name=new.name, # type: ignore
    #     position=position,
    #     is_eligible=eval_data.get("is_eligible"), # type: ignore
    #     candidate_id=new.id,# type: ignore
    #     evaluation_id=new_eval.id,# type: ignore
    #     requisition_id=requisition_id# type: ignore
    # )

    return result_candidate, task.id


async def event_stream_generator(
    files: List[UploadFile],
    job_description: str,
    request: Request,
    current_user: Any = None,
    requisition: Any = None
):
    """
    Generator that processes files and yields SSE events
    """
    results = []

    try:
        for i, file in enumerate(files):
            # Check if client disconnected
            if await request.is_disconnected():
                print("Client disconnected, stopping processing")
                break

            original_name = file.filename

            # Send progress event
            yield f"event: progress\n"
            yield f"data: {json.dumps({'index': i, 'status': 'started'})}\n\n"

            try:
                # Read file content
                content = await file.read()

                # Save to system temp directory in a cross-platform safe way

                tmp_dir = tempfile.gettempdir()

                safe_name = os.path.basename(original_name or "uploaded_file")

                name, ext = os.path.splitext(safe_name)
                with tempfile.NamedTemporaryFile(delete=False, prefix="eval_", suffix=ext, dir=tmp_dir) as tmpf:
                    tmpf.write(content)
                    temp_path = tmpf.name

                try:
                    # Process the file
                    result = await process_evaluation_job(
                        file_path=temp_path,
                        job_description=job_description,
                        current_user=current_user,
                        requisition=requisition
                    )

                    results.append({"result": result})
                finally:
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

                # Send result event
                yield f"event: result\n"
                yield f"data: {json.dumps({'index': i, 'status': 'completed', 'result': result})}\n\n"

            except Exception as err:
                error_msg = str(err)
                print(f"Error processing file {original_name}: {error_msg}")
                traceback.print_exc()

                # Send error event
                yield f"event: error\n"
                yield f"data: {json.dumps({'index': i, 'status': 'failed', 'error': error_msg})}\n\n"

        # Send done event
        yield f"event: done\n"
        yield f"data: {json.dumps({'count': len(results), 'results': results})}\n\n"

        # Send close event
        yield f"event: close\n"
        yield f"data: {{}}\n\n"

    except asyncio.CancelledError:
        print("Stream cancelled by client")
        raise
    except Exception as e:
        print(f"Unexpected error in event stream: {str(e)}")
        traceback.print_exc()
        yield f"event: error\n"
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
