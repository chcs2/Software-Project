from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/friends", tags=["friends"])


# CAMADA DE SERVIÇO (O "Cérebro" das Amizades)

class FriendService:
    async def get_user_by_email(self, db: AsyncSession, email: str):
        res = await db.execute(select(models.User).where(models.User.email == email))
        return res.scalars().first()

    async def send_request(self, db: AsyncSession, current_user_email: str, target_email: str):
        me = await self.get_user_by_email(db, current_user_email)
        
        if target_email == me.email:
            raise HTTPException(status_code=400, detail="Não podes enviar um pedido a ti mesmo.")

        target_user = await self.get_user_by_email(db, target_email)
        if not target_user:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado com esse email.")

        existing_res = await db.execute(
            select(models.Friendship).where(
                or_(
                    and_(models.Friendship.requester_id == me.id, models.Friendship.receiver_id == target_user.id),
                    and_(models.Friendship.requester_id == target_user.id, models.Friendship.receiver_id == me.id)
                )
            )
        )
        if existing_res.scalars().first():
            raise HTTPException(status_code=400, detail="Já existe um pedido de amizade ou já são amigos.")

        new_request = models.Friendship(requester_id=me.id, receiver_id=target_user.id, status="pending")
        db.add(new_request)
        await db.commit()
        return {"message": f"Pedido enviado com sucesso para {target_user.name}!"}

    async def get_pending_requests(self, db: AsyncSession, current_user_email: str):
        me = await self.get_user_by_email(db, current_user_email)

        query = select(models.Friendship, models.User).join(
            models.User, models.Friendship.requester_id == models.User.id
        ).where(
            models.Friendship.receiver_id == me.id,
            models.Friendship.status == "pending"
        )
        
        result = await db.execute(query)
        requests = [
            {
                "friendship_id": friendship.id,
                "requester_name": requester.name,
                "requester_email": requester.email
            }
            for friendship, requester in result.all()
        ]
        return requests

    async def accept_request(self, db: AsyncSession, current_user_email: str, friendship_id: int):
        me = await self.get_user_by_email(db, current_user_email)

        req_res = await db.execute(select(models.Friendship).where(models.Friendship.id == friendship_id))
        friendship = req_res.scalars().first()

        if not friendship:
            raise HTTPException(status_code=404, detail="Pedido não encontrado.")
        if friendship.receiver_id != me.id:
            raise HTTPException(status_code=403, detail="Não tens permissão para aceitar este pedido.")
        if friendship.status == "accepted":
            return {"message": "Este pedido já foi aceite."}

        friendship.status = "accepted"
        await db.commit()
        return {"message": "Pedido aceite! Agora são amigos."}

    async def decline_or_remove(self, db: AsyncSession, current_user_email: str, friendship_id: int):
        me = await self.get_user_by_email(db, current_user_email)

        res = await db.execute(select(models.Friendship).where(models.Friendship.id == friendship_id))
        f = res.scalars().first()

        if not f:
            raise HTTPException(status_code=404, detail="Registo não encontrado.")
        if f.requester_id != me.id and f.receiver_id != me.id:
            raise HTTPException(status_code=403, detail="Não tens permissão para isto.")

        await db.delete(f)
        await db.commit()
        return {"message": "Pedido recusado ou amizade removida com sucesso."}

    async def list_friends(self, db: AsyncSession, current_user_email: str):
        me = await self.get_user_by_email(db, current_user_email)

        query = select(models.Friendship).where(
            or_(models.Friendship.requester_id == me.id, models.Friendship.receiver_id == me.id),
            models.Friendship.status == "accepted"
        )
        res = await db.execute(query)
        friendships = res.scalars().all()

        friends_list = []
        for f in friendships:
            friend_id = f.receiver_id if f.requester_id == me.id else f.requester_id
            friend_res = await db.execute(select(models.User).where(models.User.id == friend_id))
            friend = friend_res.scalars().first()
            
            if friend:
                friends_list.append({
                    "friendship_id": f.id,
                    "id": friend.id,
                    "name": friend.name,
                    "email": friend.email
                })
        return friends_list

# Instanciar o serviço
friend_service = FriendService()


# ==========================================
# ROTAS (Os "Carteiros")
# ==========================================

@router.post("/request")
async def send_friend_request(req: schemas.FriendRequestCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await friend_service.send_request(db, current_user, req.email)

@router.get("/pending", response_model=list[schemas.PendingRequestResponse])
async def get_pending_requests(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await friend_service.get_pending_requests(db, current_user)

@router.post("/accept/{friendship_id}")
async def accept_friend_request(friendship_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await friend_service.accept_request(db, current_user, friendship_id)

@router.delete("/decline/{friendship_id}")
async def decline_or_remove_friendship(friendship_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await friend_service.decline_or_remove(db, current_user, friendship_id)

@router.get("/list", response_model=list[schemas.FriendInfoResponse])
async def list_friends(db: AsyncSession = Depends(get_db), current_user: str = Depends(auth.get_current_user)):
    return await friend_service.list_friends(db, current_user)