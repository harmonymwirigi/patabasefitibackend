# File: backend/app/utils/sqlite_json.py
# SQLite JSON serialization helper

import json
from sqlalchemy import event
from sqlalchemy.engine import Engine

def apply_sqlite_json_patch():
    """
    Apply a patch to SQLAlchemy to handle JSON fields properly for SQLite
    This simpler version just handles parameter serialization
    """
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Serialize JSON data in parameters
        if parameters is not None:
            # Handle single parameter sets
            if not executemany:
                if isinstance(parameters, (list, tuple)):
                    parameters = list(parameters)
                    for i, param in enumerate(parameters):
                        if isinstance(param, (dict, list)):
                            parameters[i] = json.dumps(param)
                elif isinstance(parameters, dict):
                    for key, value in list(parameters.items()):
                        if isinstance(value, (dict, list)):
                            parameters[key] = json.dumps(value)