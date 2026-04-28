# app/routers/friends.py
from fastapi import APIRouter, Depends, HTTPException
from app.database import db_conn
from app.security import get_current_user
from app.schemas import FriendActionRequest, UserSearchItem
from typing import List

router = APIRouter(prefix="/friends", tags=["Друзья"])

@router.get("/search", response_model=List[UserSearchItem])
async def search_users(query: str, current_user: str = Depends(get_current_user)):
    if len(query) < 3:
        return []

    cursor = db_conn.cursor()
    # Ищем всех, кто подходит под запрос, кроме самого себя
    cursor.execute("SELECT username FROM users WHERE username LIKE ? AND username != ? LIMIT 20", (f"%{query}%", current_user))
    users = cursor.fetchall()
    
    results = []
    for (user,) in users:
        # Проверяем статус отношений
        cursor.execute('''
            SELECT requester, status FROM friendships 
            WHERE (requester = ? AND addressee = ?) OR (requester = ? AND addressee = ?)
        ''', (current_user, user, user, current_user))
        rel = cursor.fetchone()
        
        status = 'none'
        if rel:
            if rel[1] == 'accepted':
                status = 'friends'
            elif rel[0] == current_user:
                status = 'pending_sent'
            else:
                status = 'pending_received'
                
        results.append(UserSearchItem(username=user, status=status))
        
    return results

@router.post("/request")
async def send_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user)):
    target = req.target_username
    cursor = db_conn.cursor()
    
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (target,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    cursor.execute('''
        SELECT status FROM friendships 
        WHERE (requester = ? AND addressee = ?) OR (requester = ? AND addressee = ?)
    ''', (current_user, target, target, current_user))
    
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Заявка уже существует или вы уже друзья")

    cursor.execute("INSERT INTO friendships (requester, addressee, status) VALUES (?, ?, 'pending')", 
                   (current_user, target))
    db_conn.commit()
    return {"message": "Заявка отправлена"}

@router.post("/accept")
async def accept_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user)):
    cursor = db_conn.cursor()
    # Подтвердить может только тот, кому заявка была адресована
    cursor.execute('''
        UPDATE friendships SET status = 'accepted' 
        WHERE requester = ? AND addressee = ? AND status = 'pending'
    ''', (req.target_username, current_user))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Нет активной заявки от этого пользователя")
        
    db_conn.commit()
    return {"message": "Заявка принята, теперь вы друзья"}

@router.get("/list")
async def get_friends_list(current_user: str = Depends(get_current_user)):
    cursor = db_conn.cursor()
    cursor.execute('''
        SELECT requester FROM friendships WHERE addressee = ? AND status = 'accepted'
        UNION
        SELECT addressee FROM friendships WHERE requester = ? AND status = 'accepted'
    ''', (current_user, current_user))
    
    friends = [row[0] for row in cursor.fetchall()]
    # Импортируем менеджер здесь (локально), чтобы избежать циклических импортов
    from app.ws_manager import manager 
    
    # Возвращаем список друзей и их статус в сети
    return [{"username": f, "online": f in manager.active_connections} for f in friends]