from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List

from api.db.database import get_db
from api.logs.logger import logger
from api.auth.dependencies import get_admin_user
from api.auth.scopes import Scopes, get_user_with_scopes
from api.db.models import User
from . import schemas, crud
from api.users import crud as user_crud
from api.users.auth import get_current_admin_user
from api.users.schemas import UserCreate, UserUpdate, UserRead

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

@router.get("/dashboard", response_model=schemas.AdminDashboard)
async def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_READ))
):
    """
    Get admin dashboard data including user statistics and recent activity.
    Requires admin privileges with admin:read scope.
    """
    dashboard_data = crud.get_admin_dashboard(db)
    
    # Log access
    logger.info(f"Admin {current_user.username} accessed the dashboard")
    
    return dashboard_data

@router.get("/users", response_model=List[UserRead])
def get_all_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_READ, Scopes.USER_READ))
):
    """
    Get all users (admin only)
    Requires admin:read and user:read scopes.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info(f"Admin {current_user.username} retrieved user list with {len(users)} users")
    return users

@router.get("/users/{user_id}", response_model=UserRead)
def get_specific_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_READ, Scopes.USER_READ))
):
    """
    Get a specific user by ID (admin only)
    Requires admin:read and user:read scopes.
    """
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Admin {current_user.username} retrieved details for user {user.username}")
    return user

@router.post("/users", response_model=UserRead)
def create_user_admin(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_WRITE, Scopes.USER_WRITE))
):
    """
    Create a new user (admin only)
    Requires admin:write and user:write scopes.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    return crud.create_user(db=db, user=user)

@router.put("/users/{user_id}", response_model=UserRead)
def update_user_admin(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_WRITE, Scopes.USER_WRITE))
):
    """
    Update a user (admin only)
    Requires admin:write and user:write scopes.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.update_user(db=db, user_id=user_id, user_update=user_update)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_DELETE, Scopes.USER_DELETE))
):
    """
    Delete a user (admin only)
    Requires admin:delete and user:delete scopes.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud.delete_user(db=db, user_id=user_id)
    logger.info(f"Admin {current_user.username} deleted user {db_user.username}")
    return None

@router.get("/stats", response_model=dict)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_READ, Scopes.STATS_READ))
):
    """
    Get user statistics (admin only)
    Requires admin:read and stats:read scopes.
    """
    total_users = crud.count_users(db)
    active_users = crud.count_active_users(db)
    admin_users = crud.count_admin_users(db)
    
    # Get the latest registered users
    recent_users = crud.get_recent_users(db, limit=5)
    recent_user_data = [
        {"id": user.id, "username": user.username, "created_at": user.created_at}
        for user in recent_users
    ]
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "recent_users": recent_user_data
    }

@router.get("/logs", response_model=List[schemas.ActivityLog])
async def admin_get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_with_scopes(Scopes.ADMIN_READ, Scopes.LOGS_READ))
):
    """
    Get global activity logs.
    Requires admin:read and logs:read scopes.
    """
    logs = crud.get_recent_activity_logs(db=db)
    logger.info(f"Admin {current_user.username} retrieved {len(logs)} activity logs")
    return logs 