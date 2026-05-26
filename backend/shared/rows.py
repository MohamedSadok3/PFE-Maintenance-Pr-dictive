"""Convert PostgreSQL rows (RealDictCursor) to plain dicts for services and serializers."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional


def row_to_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    data = dict(row)
    for key, value in data.items():
        if isinstance(value, (datetime, date)):
            data[key] = value.isoformat()
    return data


def rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [row_to_dict(row) for row in rows if row]
