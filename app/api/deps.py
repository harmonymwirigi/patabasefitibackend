# For backwards compatibility, we are re-exporting the dependencies here
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_owner_user,
    get_current_admin_user
)
from app.db.database import get_db