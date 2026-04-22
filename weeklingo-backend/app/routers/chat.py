from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/chat", tags=["chat"])


# CLASSE: ChatService (O Tutor de IA)

class ChatService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        
        self.instrucao_tutor = """
        You are a friendly and encouraging English language tutor. 
        Have a natural conversation with the user in English.
        If the user makes a grammar, spelling, or vocabulary mistake, reply naturally to keep the conversation going. 
        Then, at the very end of your response, add a new line with the exact tag '[CORREÇÃO]' 
        followed by a brief, polite explanation of their mistake in Portuguese.
        If there are no mistakes, do not include the '[CORREÇÃO]' tag.
        """
        # O estado (histórico) agora pertence ao objeto, não fica solto no ficheiro
        self.historico_chat = [{"role": "system", "content": self.instrucao_tutor}]

    def is_ready(self):
        return self.client is not None

    def get_reply(self, user_message: str) -> str:
        self.historico_chat.append({"role": "user", "content": user_message})
        
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=self.historico_chat,
            temperature=0.7,
            max_tokens=1024
        )
        resposta_texto = completion.choices[0].message.content
        self.historico_chat.append({"role": "assistant", "content": resposta_texto})
        return resposta_texto

# Instanciamos o Tutor
tutor = ChatService()

class ChatMessage(BaseModel):
    message: str

# ROTAS (Agora super limpas, apenas delegam trabalho ao Tutor)
@router.post("/send")
async def send_message(req: ChatMessage):
    if not tutor.is_ready():
        raise HTTPException(status_code=500, detail="Motor de IA não configurado.")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="A mensagem não pode estar vazia.")
        
    try:
        resposta = tutor.get_reply(req.message)
        return {"reply": resposta}
    except Exception as e:
        print(f"🔴 Erro na API da Groq: {e}")
        raise HTTPException(status_code=500, detail="O Tutor Groq está com dificuldades técnicas.")