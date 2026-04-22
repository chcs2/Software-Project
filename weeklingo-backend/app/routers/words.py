from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, not_, func
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/words", tags=["words"])


# CLASSE: WordService (Gestor de Vocabulário)

class WordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quiz_words(self, email: str):
        user_res = await self.db.execute(select(models.User).where(models.User.email == email))
        user = user_res.scalars().first()

        learned_query = select(models.Progress.word_id).where(models.Progress.user_id == user.id)
        learned_ids = (await self.db.execute(learned_query)).scalars().all()

        query = select(models.Word).where(not_(models.Word.id.in_(learned_ids))).order_by(func.random())
        return (await self.db.execute(query)).scalars().all()

    async def create_word(self, word_data: schemas.WordCreate):
        new_word = models.Word(**word_data.model_dump())
        self.db.add(new_word)
        await self.db.commit()
        await self.db.refresh(new_word)
        return new_word

    async def get_all(self):
        return (await self.db.execute(select(models.Word))).scalars().all()

    async def get_one(self, word_id: int):
        word = (await self.db.execute(select(models.Word).where(models.Word.id == word_id))).scalars().first()
        if not word:
            raise HTTPException(status_code=404, detail="Palavra não encontrada.")
        return word

    async def update(self, word_id: int, update_data: schemas.WordUpdate):
        db_word = await self.get_one(word_id)
        
        if update_data.english_word: db_word.english_word = update_data.english_word
        if update_data.portuguese_translation: db_word.portuguese_translation = update_data.portuguese_translation
        if update_data.category: db_word.category = update_data.category
            
        await self.db.commit()
        await self.db.refresh(db_word)
        return db_word

    async def delete(self, word_id: int):
        db_word = await self.get_one(word_id)
        await self.db.delete(db_word)
        await self.db.commit()
        return {"message": "Palavra apagada com sucesso!"}

# ROTAS
@router.get("/quiz", response_model=list[schemas.WordResponse])
async def get_quiz_words(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).get_quiz_words(current_user)

@router.post("/", response_model=schemas.WordResponse)
async def create_word(word: schemas.WordCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).create_word(word)

@router.get("/", response_model=list[schemas.WordResponse])
async def read_words(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).get_all()

@router.get("/{word_id}", response_model=schemas.WordResponse)
async def read_word(word_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).get_one(word_id)

@router.put("/{word_id}", response_model=schemas.WordResponse)
async def update_word(word_id: int, word_update: schemas.WordUpdate, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).update(word_id, word_update)

@router.delete("/{word_id}")
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await WordService(db).delete(word_id)