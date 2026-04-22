from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, auth
from app.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/mistakes", tags=["mistakes"])

class MistakeCreate(BaseModel):
    word_id: int


# CLASSE: MistakeService (Gestor de Erros)

class MistakeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        user_res = await self.db.execute(select(models.User).where(models.User.email == email))
        return user_res.scalars().first()

    async def register_mistake(self, email: str, word_id: int):
        user = await self.get_user_by_email(email)
        if not user:
            return {"message": "Utilizador não encontrado."}

        existing_res = await self.db.execute(
            select(models.Mistake).where(
                models.Mistake.user_id == user.id,
                models.Mistake.word_id == word_id
            )
        )
        if existing_res.scalars().first():
            return {"message": "Erro já estava registado."}

        new_mistake = models.Mistake(user_id=user.id, word_id=word_id)
        self.db.add(new_mistake)
        await self.db.commit()
        return {"message": "Palavra adicionada à lista de revisão."}

    async def get_my_mistakes(self, email: str):
        user = await self.get_user_by_email(email)
        result = await self.db.execute(
            select(models.Word).join(models.Mistake).where(models.Mistake.user_id == user.id)
        )
        return result.scalars().all()

# ROTAS
@router.post("/")
async def register_mistake(
    mistake: MistakeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(auth.get_current_user)
):
    service = MistakeService(db)
    return await service.register_mistake(current_user, mistake.word_id)

@router.get("/")
async def get_my_mistakes(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(auth.get_current_user)
):
    service = MistakeService(db)
    return await service.get_my_mistakes(current_user)