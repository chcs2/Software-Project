import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()


# CLASSE: AuthService (O Segurança)

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "chave-secreta-muito-segura-123")
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=60)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise ValueError("Email não encontrado no token")
            return email
        except Exception:
            raise ValueError("Token inválido ou expirado")

# Instância global do serviço para as rotas usarem
auth_service = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Mantemos esta função para o FastAPI usar no Depends()
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return auth_service.decode_token(token)
    except ValueError:
        raise credentials_exception