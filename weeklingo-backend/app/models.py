from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Importa a Classe Mãe do nosso ficheiro database.py

# A classe User herda de Base. Isto significa que é uma tabela de base de dados.
class User(Base):
    __tablename__ = "users" # O nome exato da tabela no PostgreSQL

    # Definimos as colunas como atributos da Classe
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # server_default=func.now() diz ao PostgreSQL para colocar a data/hora atual automaticamente.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Campos da Meta Semanal
    weekly_goal = Column(Integer, default=10)
    goal_set_at = Column(DateTime(timezone=True), nullable=True)

    # RELAÇÕES (Isto é magia OO)
    # Permite-nos fazer algo como 'user.mistakes' no código e o Python vai buscar 
    # todos os erros daquele utilizador automaticamente, sem escrevermos código SQL.
    progress = relationship("Progress", back_populates="owner")
    mistakes = relationship("Mistake", back_populates="user")

    def __repr__(self):
        """
        Método Mágico de Representação (__repr__).
        Se fizeres print(utilizador) no terminal, em vez de veres lixo na memória do computador,
        vais ver algo bonito e útil como: <User(name='Tiago', email='tiago@email.com')>
        """
        return f"<User(name='{self.name}', email='{self.email}')>"


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    english_word = Column(String, index=True, nullable=False)
    portuguese_translation = Column(String, nullable=False)
    category = Column(String, index=True)

    def __repr__(self):
        return f"<Word('{self.english_word}' -> '{self.portuguese_translation}')>"


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    # ForeignKey liga esta linha a um Utilizador específico
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ForeignKey liga esta linha a uma Palavra específica
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    is_learned = Column(Boolean, default=True)
    learned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Configuração de volta das relações
    owner = relationship("User", back_populates="progress")
    word = relationship("Word")


class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="mistakes")
    word = relationship("Word")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String, default="pending") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # foreign_keys é obrigatório aqui porque temos DUAS ligações para a mesma tabela (User)
    requester = relationship("User", foreign_keys=[requester_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

    def __repr__(self):
        return f"<Friendship(de:{self.requester_id} para:{self.receiver_id} status:{self.status})>"