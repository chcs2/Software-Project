from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


# CAMADA DE SERVIÇO (O "Cérebro" dos Users)

class UserService:
    async def get_user_me_details(self, db: AsyncSession, email: str):
        result = await db.execute(select(models.User).where(models.User.email == email))
        db_user = result.scalars().first()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
            
        # Contagem total de palavras aprendidas
        count_result = await db.execute(
            select(func.count(models.Progress.id)).where(models.Progress.user_id == db_user.id)
        )
        total_learned = count_result.scalar()

        return {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at,
            "weekly_goal": db_user.weekly_goal,
            "goal_set_at": db_user.goal_set_at,
            "total_learned": total_learned
        }

    async def get_goal(self, db: AsyncSession, email: str):
        result = await db.execute(select(models.User).where(models.User.email == email))
        db_user = result.scalars().first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
        return {"weekly_goal": db_user.weekly_goal, "goal_set_at": db_user.goal_set_at}

    async def set_goal(self, db: AsyncSession, email: str, goal: int):
        result = await db.execute(select(models.User).where(models.User.email == email))
        db_user = result.scalars().first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

        # Lógica de bloqueio semanal
        hoje = datetime.now(timezone.utc)
        dias_desde_domingo = (hoje.weekday() + 1) % 7 
        inicio_semana = hoje - timedelta(days=dias_desde_domingo)
        inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)

        if db_user.goal_set_at:
            set_at = db_user.goal_set_at
            if set_at.tzinfo is None:
                set_at = set_at.replace(tzinfo=timezone.utc)
            if set_at >= inicio_semana:
                raise HTTPException(
                    status_code=400, 
                    detail="A meta já foi definida esta semana e só pode ser alterada após o reset de domingo."
                )

        db_user.weekly_goal = goal
        db_user.goal_set_at = hoje
        await db.commit()
        await db.refresh(db_user)
        return {"message": "Meta atualizada com sucesso", "goal": db_user.weekly_goal}

    async def create_user(self, db: AsyncSession, user_data: schemas.UserCreate):
        query = select(models.User).where(models.User.email == user_data.email)
        result = await db.execute(query)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Este email já existe.")

        # AQUI usamos o serviço de autenticação de forma segura!
        hashed_pw = auth.auth_service.get_password_hash(user_data.password)
        new_user = models.User(name=user_data.name, email=user_data.email, password_hash=hashed_pw)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def update_user(self, db: AsyncSession, user_id: int, user_update: schemas.UserUpdate):
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        db_user = result.scalars().first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
        
        if user_update.name: db_user.name = user_update.name
        if user_update.email: db_user.email = user_update.email
        if user_update.password:
            # Corrigido o bug do código antigo aqui!
            db_user.password_hash = auth.auth_service.get_password_hash(user_update.password)
            
        await db.commit()
        await db.refresh(db_user)
        return db_user

# Instanciar o serviço
user_service = UserService()



# ROTAS (Os "Carteiros")


@router.get("/me", response_model=schemas.UserResponse)
async def read_user_me(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await user_service.get_user_me_details(db, current_user)

@router.get("/me/goal")
async def get_user_goal(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await user_service.get_goal(db, current_user)

@router.post("/me/goal")
async def set_user_goal(goal: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await user_service.set_goal(db, current_user, goal)

@router.post("/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await user_service.create_user(db, user)

@router.get("/", response_model=list[schemas.UserResponse])
async def read_users(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    result = await db.execute(select(models.User))
    return result.scalars().all()

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(user_id: int, user_update: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    return await user_service.update_user(db, user_id, user_update)

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    await db.delete(user)
    await db.commit()
    return {"message": "Utilizador apagado com sucesso!"}