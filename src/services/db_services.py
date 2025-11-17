import datetime
import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from src.models.evaluations import Evaluation

def get_recent_entries_sql(db: Session) -> Dict[str, Any]:
    try:
        start_of_today = datetime.datetime.now(tz=datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        stmt = select(Evaluation).where(Evaluation.created_at >= start_of_today).order_by(desc(Evaluation.created_at))
        rows = db.execute(stmt).scalars().all()

        # convert ORM objects to dicts if needed (e.g. with pydantic schema)
        data: List[dict] = [row.to_dict() if hasattr(row, "to_dict") else row.__dict__ for row in rows]

        return {"success": True, "data": data}
    except Exception as e:
        logging.exception("Error in get_recent_entries_sql")
        return {"success": False, "error": str(e)}