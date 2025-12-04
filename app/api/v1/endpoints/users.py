from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api import deps
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.utils.logger import get_logger

router = APIRouter()

logger = get_logger(__name__)

@router.post("/", response_model=UserSchema)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Create new user (Organizer only).
    """
    logger.info("Organizer %s attempting to create user %s", current_user.id, user_in.email)
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        logger.warning("Organizer %s attempted to create duplicate user %s", current_user.id, user_in.email)
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await crud_user.create(db, obj_in=user_in)
    logger.info("Organizer %s created user %s with role %s", current_user.id, user.id, user.role)
    return user

@router.put("/{id}", response_model=UserSchema)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Update a user.
    """
    logger.info("Organizer %s updating user %s", current_user.id, id)
    user = await crud_user.get(db=db, id=id)
    if not user:
        logger.warning("User %s not found for update", id)
        raise HTTPException(status_code=404, detail="User not found")
    user = await crud_user.update(db=db, db_obj=user, obj_in=user_in)
    logger.info("User %s updated by organizer %s", id, current_user.id)
    return user

@router.delete("/{id}", response_model=UserSchema)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Delete a user.
    """
    logger.info("Organizer %s deleting user %s", current_user.id, id)
    user = await crud_user.get(db=db, id=id)
    if not user:
        logger.warning("User %s not found for deletion", id)
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        logger.warning("Organizer %s attempted to delete themselves", current_user.id)
        raise HTTPException(status_code=400, detail="Organizers cannot delete themselves")
    user = await crud_user.remove(db=db, id=id)
    logger.info("User %s deleted by organizer %s", id, current_user.id)
    return user
