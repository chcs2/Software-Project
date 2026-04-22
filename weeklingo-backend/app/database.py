import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# 1. Lê o ficheiro .env e carrega as variáveis (como a password da base de dados) para a memória
load_dotenv()

# 2. 'Base' é a Classe Mãe. Todas as nossas tabelas em models.py vão herdar as características dela.
Base = declarative_base()


# CLASSE: DatabaseManager (O Porteiro)

class DatabaseManager:
    """
    Esta classe encapsula a ligação à base de dados.
    Isto é OO puro: escondemos a complexidade dentro do objeto e expomos apenas o que é necessário.
    """
    def __init__(self, db_url: str):
        # O método __init__ é o construtor. Roda automaticamente quando criamos o objeto.
        self.db_url = db_url
        if not self.db_url:
            print("⚠️ AVISO: DATABASE_URL não encontrada no .env")
        
        # 'engine' é o motor do carro. Ele sabe como falar com o PostgreSQL.
        # O prefixo '_' (underscore) indica que esta variável é "privada" (só deve ser usada dentro desta classe).
        self._engine = create_async_engine(self.db_url, echo=True)
        
        # 'session_factory' é a fábrica que cria novas conversas (sessões) com o banco de dados.
        # autocommit=False garante que só guardamos os dados quando dissermos explicitamente "commit()".
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def get_db(self):
        """
        Este método é usado pelas rotas (ex: /login) para pedir uma sessão à base de dados.
        Usamos o 'yield' em vez de 'return' porque queremos que o FastAPI use a sessão
        e, depois de terminar, volte aqui para o 'finally' e feche a porta (.close()).
        """
        async with self._session_factory() as session:
            try:
                # Entrega a sessão ao utilizador/rota
                yield session
            finally:
                # Garante que a sessão é fechada, mesmo que dê erro!
                # Isto impede que a aplicação bloqueie por excesso de ligações.
                await session.close()

# 3. Criamos a instância (o objeto vivo) do nosso gestor, passando o URL da base de dados.
db_manager = DatabaseManager(os.getenv("DATABASE_URL"))

# 4. Criamos um "atalho" para a função get_db, para que o resto do teu código 
# continue a funcionar sem teres de alterar as rotas.
get_db = db_manager.get_db

# 5. [CORREÇÃO DO DOMINÓ] Exportamos o motor para a main.py não chorar
# Isto permite que a main.py continue a importar 'engine' para criar as tabelas no arranque.
engine = db_manager._engine