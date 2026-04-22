from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, words, progress, auth_routes, mistakes, friends, chat 

app = FastAPI(title="WeekLingo API")


# CONFIGURAÇÃO DO CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)


# INICIALIZAÇÃO DA BASE DE DADOS

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Descomenta a linha abaixo apenas UMA VEZ se precisares de resetar a DB inteira
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# REGISTO DAS ROTAS (Routers)

app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(words.router)
app.include_router(progress.router)
app.include_router(mistakes.router)
app.include_router(friends.router) 
app.include_router(chat.router)

@app.get("/")
def home():
    return {"mensagem": "API do WeekLingo ativa e estruturada com Sucesso!"}