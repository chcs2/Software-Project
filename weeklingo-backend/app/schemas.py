from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# ==========================================
# USERS (Utilizadores)
# ==========================================

# Schema para CRIAR um utilizador (recebe do Frontend na página de Registo)
class UserCreate(BaseModel):
    name: str
    email: str
    password: str # Recebemos a password pura aqui para ser encriptada depois

# Schema para RESPONDER ao Frontend (esconde a password por segurança!)
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    
    weekly_goal: int = 10
    # Optional significa que este campo pode ser nulo (None)
    goal_set_at: Optional[datetime] = None
    total_learned: int = 0

    # Esta configuração (model_config) é OBRIGATÓRIA para enviar dados da BD (SQLAlchemy) 
    # diretamente para o formato JSON (FastAPI/Frontend) de forma automática.
    model_config = ConfigDict(from_attributes=True)

# Schema para ATUALIZAR dados (tudo é opcional, o utilizador pode mudar só o nome, por exemplo)
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


# WORDS (Vocabulário)

class WordCreate(BaseModel):
    english_word: str
    portuguese_translation: str
    category: Optional[str] = None

class WordResponse(BaseModel):
    id: int
    english_word: str
    portuguese_translation: str
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class WordUpdate(BaseModel):
    english_word: Optional[str] = None
    portuguese_translation: Optional[str] = None
    category: Optional[str] = None


# PROGRESS (Progresso das Aulas)

class ProgressCreate(BaseModel):
    word_id: int
    is_learned: bool = True

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    word_id: int
    is_learned: bool
    learned_at: datetime

    model_config = ConfigDict(from_attributes=True)


# FRIENDSHIPS (Comunidade)

class FriendRequestCreate(BaseModel):
    email: str 

class FriendshipResponse(BaseModel):
    id: int
    requester_id: int
    receiver_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PendingRequestResponse(BaseModel):
    friendship_id: int
    requester_name: str
    requester_email: str

class FriendInfoResponse(BaseModel):
    friendship_id: int
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)