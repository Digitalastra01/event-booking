from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api import deps
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter()

@router.delete("/{id}", response_model=UserSchema)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Delete a user.
    """
    user = await crud_user.get(db=db, id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    user = await crud_user.remove(db=db, id=id)
    return user
