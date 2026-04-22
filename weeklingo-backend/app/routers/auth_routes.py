from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, auth  # Aqui ele importa o ficheiro auth
from app.database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # 1. Procura o utilizador pelo email
    query = select(models.User).where(models.User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    # 2. Verifica se existe e se a password (bcrypt) bate certo
    # ⬇️ AQUI ESTÁ A CORREÇÃO (auth.auth_service em vez de apenas auth) ⬇️
    if not user or not auth.auth_service.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou password incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Gera o token usando o nosso serviço seguro
    # ⬇️ AQUI ESTÁ A OUTRA CORREÇÃO (auth.auth_service) ⬇️
    access_token = auth.auth_service.create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}