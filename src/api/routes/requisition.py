from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Any, cast, Optional
from ..deps import get_current_active_user
from src.models.Requisition import Requisition
from src.db.init_db import get_db
from src.schemas.requisition import RequisitionCreate, RequisitionCreateResponse, ListRequisitionsResponse
from sqlalchemy.exc import IntegrityError
import re
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID


router = APIRouter()


@router.post("/newrequisition", response_model=RequisitionCreateResponse, status_code=status.HTTP_201_CREATED)
def add_requisition(requisition: RequisitionCreate, current_user: Any = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Normalize input
    title = (requisition.requisition or "").strip()
    description = (requisition.description or "").strip()

    # Basic validations
    title_regex = r"^[A-Za-z0-9\s]{2,100}$"
    if not re.match(title_regex, title):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Requisition must be 2-100 characters and contain only letters, numbers and spaces"
        )

    new_requisition = Requisition(
        requisition=title,
        description=description,
        created_by=current_user.id
    )

    try:
        db.add(new_requisition)
        db.commit()
        db.refresh(new_requisition)
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database integrity error: possible duplicate or constraint violation"
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the requisition"
        )

    return {
        "success": True,
        "requisition": new_requisition
    }


@router.get("/requisitions", response_model=ListRequisitionsResponse, status_code=status.HTTP_200_OK)
def list_requisitions(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List requisitions created by the current user with pagination and search.

    - skip: number of items to skip (>= 0)
    - limit: max items to return (1..1000)
    - search: optional search term to filter by requisition title or description
    """

    # Validate pagination params
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="skip must be a non-negative integer",
        )

    max_limit = 1000
    if limit <= 0 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"limit must be between 1 and {max_limit}",
        )

    try:
        # Build base query filtered by current user
        base_query = db.query(Requisition).filter(
            Requisition.created_by == current_user.id
        )

        # Apply search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            base_query = base_query.filter(
                (Requisition.requisition.ilike(search_term)) |
                (Requisition.description.ilike(search_term))
            )

        # Debug prints to help trace behavior
        print(
            f"[debug] list_requisitions called by user id={getattr(current_user, 'id', None)}")
        print(
            f"[debug] pagination params: skip={skip}, limit={limit}, search={search}")
        try:
            total = base_query.count()
            print(f"[debug] base_query count={total}")
        except Exception as e:
            # non-fatal — just print and continue
            print(f"[debug] failed to count base_query: {e}")

        # Return requisitions newest first
        requisitions = base_query.order_by(
            Requisition.created_at.desc()).offset(skip).limit(limit).all()

        print(f"[debug] fetched requisitions: {len(requisitions)}")
        if requisitions:
            print("[debug] requisition ids:", [str(r.id)
                  for r in requisitions])

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving requisitions",
        )

    # Response model expects {'success': bool, 'requisitions': list[...]}
    return {"success": True, "requisitions": requisitions}


@router.get("/requisitions/{requisition_id}", status_code=status.HTTP_200_OK)
def get_requisition(
    requisition_id: UUID,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single requisition by ID.
    Only the creator of the requisition can retrieve it.
    """
    try:
        requisition = db.query(Requisition).filter(
            Requisition.id == requisition_id,
            Requisition.created_by == current_user.id
        ).first()

        if not requisition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requisition not found or access denied"
            )

        return {"success": True, "requisition": requisition}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the requisition"
        )


@router.put("/requisitions/{requisition_id}", status_code=status.HTTP_200_OK)
def update_requisition(
    requisition_id: UUID,
    requisition_data: RequisitionCreate,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a requisition by ID.
    Only the creator can update it.
    """
    try:
        requisition = db.query(Requisition).filter(
            Requisition.id == requisition_id,
            Requisition.created_by == current_user.id
        ).first()

        if not requisition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requisition not found or access denied"
            )

        # Normalize and validate input
        title = (requisition_data.requisition or "").strip()
        description = (requisition_data.description or "").strip()

        title_regex = r"^[A-Za-z0-9\s]{2,100}$"
        if not re.match(title_regex, title):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Requisition must be 2-100 characters and contain only letters, numbers and spaces"
            )

        # Update fields
        requisition.requisition = title  # type: ignore
        requisition.description = description  # type: ignore

        db.commit()
        db.refresh(requisition)

        return {"success": True, "requisition": requisition}

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database integrity error: possible constraint violation"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the requisition"
        )


@router.delete("/requisitions/{requisition_id}", status_code=status.HTTP_200_OK)
def delete_requisition(
    requisition_id: UUID,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a requisition by ID.
    Only the creator can delete it.
    Cascading delete will remove associated evaluations.
    """
    try:
        requisition = db.query(Requisition).filter(
            Requisition.id == requisition_id,
            Requisition.created_by == current_user.id
        ).first()

        if not requisition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requisition not found or access denied"
            )

        db.delete(requisition)
        db.commit()

        return {"success": True, "message": "Requisition deleted successfully"}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the requisition"
        )
