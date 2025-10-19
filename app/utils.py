"""
Utility functions
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date, time
import json

def format_date(d: date) -> str:
    return d.strftime("%B %d, %Y")

def format_time(t: time) -> str:
    return datetime.combine(date.today(), t).strftime("%I:%M %p")

def format_datetime(dt: datetime) -> dict:
    return {
        "date": format_date(dt.date()),
        "time": format_time(dt.time()),
        "timestamp": dt.isoformat()
    }

def build_query_filters(base_query: str, filters: Dict[str, Any]) -> tuple:
    query = base_query
    params = []
    for key, value in filters.items():
        if value is not None:
            if isinstance(value, str) and "%" in value:
                query += f" AND {key} ILIKE %s"
            else:
                query += f" AND {key} = %s"
            params.append(value)
    return query, params

def paginate(query: str, limit: int = 100, offset: int = 0) -> str:
    return f"{query} LIMIT {limit} OFFSET {offset}"

def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return value
    return value

def success_response(message: str, data: Any = None) -> dict:
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response

def error_response(message: str, details: Any = None) -> dict:
    response = {"success": False, "error": message}
    if details is not None:
        response["details"] = details
    return response
