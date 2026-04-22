from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app import models, schemas, auth
from app.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/progress", tags=["progress"])


# CLASSE: ProgressService (Gestor de Progresso)

class ProgressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        res = await self.db.execute(select(models.User).where(models.User.email == email))
        return res.scalars().first()

    async def mark_as_learned(self, email: str, word_id: int):
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

        word_exists = await self.db.execute(select(models.Word).where(models.Word.id == word_id))
        if not word_exists.scalars().first():
            raise HTTPException(status_code=404, detail="Palavra não encontrada.")

        # Remove dos erros se existir
        mistake_query = select(models.Mistake).where(
            models.Mistake.user_id == user.id, models.Mistake.word_id == word_id
        )
        mistake_to_delete = (await self.db.execute(mistake_query)).scalars().first()
        if mistake_to_delete:
            await self.db.delete(mistake_to_delete)

        # Regista Progresso
        progress_exists = await self.db.execute(
            select(models.Progress).where(
                models.Progress.user_id == user.id, models.Progress.word_id == word_id
            )
        )
        existing = progress_exists.scalars().first()
        if existing:
            await self.db.commit()
            return existing

        new_progress = models.Progress(user_id=user.id, word_id=word_id)
        self.db.add(new_progress)
        await self.db.commit()
        await self.db.refresh(new_progress)
        return new_progress

    async def get_weekly_count(self, email: str):
        user = await self.get_user_by_email(email)
        agora = datetime.now()
        dias_desde_domingo = (agora.weekday() + 1) % 7
        inicio_semana = (agora - timedelta(days=dias_desde_domingo)).replace(hour=0, minute=0, second=0, microsecond=0)

        query = select(func.count(models.Progress.id)).where(
            models.Progress.user_id == user.id, models.Progress.learned_at >= inicio_semana
        )
        total = (await self.db.execute(query)).scalar()
        return {"total_semana": total}

    async def get_my_learned(self, email: str):
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
        result = await self.db.execute(select(models.Progress).where(models.Progress.user_id == user.id))
        return result.scalars().all()

    async def get_by_id(self, user_id: int):
        result = await self.db.execute(select(models.Progress).where(models.Progress.user_id == user_id))
        return result.scalars().all()

# ROTAS
@router.post("/", response_model=schemas.ProgressResponse)
async def mark_word_as_learned(progress: schemas.ProgressCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await ProgressService(db).mark_as_learned(current_user, progress.word_id)

@router.get("/weekly")
async def get_weekly_count(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await ProgressService(db).get_weekly_count(current_user)

@router.get("/me", response_model=list[schemas.ProgressResponse])
async def get_my_learned_words(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await ProgressService(db).get_my_learned(current_user)

@router.get("/user/{user_id}", response_model=list[schemas.ProgressResponse])
async def get_learned_words_by_id(user_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await ProgressService(db).get_by_id(user_id)