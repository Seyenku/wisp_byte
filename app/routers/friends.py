from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.database import get_db_session
from app.security import get_current_user
from app.schemas import FriendActionRequest, UserSearchItem, FriendSuggestion
from app.models import User, Friendship
from typing import List

router = APIRouter(prefix="/friends", tags=["Друзья"])

@router.get("/search", response_model=List[UserSearchItem])
async def search_users(query: str, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    if len(query) < 3:
        return []

    # Экранирование спецсимволов для безопасности ilike
    safe_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

    # Поиск пользователей
    result = await session.execute(
        select(User.username)
        .where(User.username.ilike(f"%{safe_query}%"))
        .where(User.username != current_user)
        .limit(20)
    )
    usernames = result.scalars().all()

    if not usernames:
        return []

    # Оптимизация N+1: получаем все связи текущего пользователя с найденными за один запрос
    rel_result = await session.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.requester == current_user, Friendship.addressee.in_(usernames)),
                and_(Friendship.addressee == current_user, Friendship.requester.in_(usernames))
            )
        )
    )
    friendships = rel_result.scalars().all()
    
    # Создаем мапу для быстрого доступа
    rel_map = {}
    for f in friendships:
        other = f.addressee if f.requester == current_user else f.requester
        rel_map[other] = f

    results = []
    for username in usernames:
        rel = rel_map.get(username)
        status = 'none'
        if rel:
            if rel.status == 'accepted':
                status = 'friends'
            elif rel.requester == current_user:
                status = 'pending_sent'
            else:
                status = 'pending_received'
        
        results.append(UserSearchItem(username=username, status=status))

    return results

@router.post("/request")
async def send_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    target = req.target_username
    
    if target == current_user:
        raise HTTPException(status_code=400, detail="Нельзя добавить самого себя")
    
    user_result = await session.execute(select(User).where(User.username == target))
    if not user_result.scalars().first():
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    rel_result = await session.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.requester == current_user, Friendship.addressee == target),
                and_(Friendship.requester == target, Friendship.addressee == current_user)
            )
        )
    )
    
    if rel_result.scalars().first():
        raise HTTPException(status_code=400, detail="Заявка уже существует или вы уже друзья")

    new_friendship = Friendship(requester=current_user, addressee=target, status="pending")
    session.add(new_friendship)
    await session.commit()
    
    # WebSocket уведомление (если пользователь онлайн)
    from app.ws_manager import manager
    await manager.notify_user(target, {"system": "friend_request", "from": current_user})
    
    return {"message": "Заявка отправлена"}

@router.post("/accept")
async def accept_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    rel_result = await session.execute(
        select(Friendship).where(
            and_(
                Friendship.requester == req.target_username,
                Friendship.addressee == current_user,
                Friendship.status == 'pending'
            )
        )
    )
    friendship = rel_result.scalars().first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Активная заявка не найдена")

    friendship.status = 'accepted'
    await session.commit()
    
    # Уведомляем отправителя, что его приняли
    from app.ws_manager import manager
    await manager.notify_user(req.target_username, {"system": "request_accepted", "from": current_user})
    
    return {"message": "Заявка принята"}

@router.post("/reject")
async def reject_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    rel_result = await session.execute(
        select(Friendship).where(
            and_(
                Friendship.requester == req.target_username,
                Friendship.addressee == current_user,
                Friendship.status == 'pending'
            )
        )
    )
    friendship = rel_result.scalars().first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    await session.delete(friendship)
    await session.commit()
    return {"message": "Заявка отклонена"}

@router.post("/cancel")
async def cancel_friend_request(req: FriendActionRequest, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    rel_result = await session.execute(
        select(Friendship).where(
            and_(
                Friendship.requester == current_user,
                Friendship.addressee == req.target_username,
                Friendship.status == 'pending'
            )
        )
    )
    friendship = rel_result.scalars().first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    await session.delete(friendship)
    await session.commit()
    return {"message": "Заявка отозвана"}

@router.post("/remove")
async def remove_friend(req: FriendActionRequest, current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    rel_result = await session.execute(
        select(Friendship).where(
            and_(
                or_(
                    and_(Friendship.requester == current_user, Friendship.addressee == req.target_username),
                    and_(Friendship.requester == req.target_username, Friendship.addressee == current_user)
                ),
                Friendship.status == 'accepted'
            )
        )
    )
    friendship = rel_result.scalars().first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Друг не найден")
    
    await session.delete(friendship)
    await session.commit()
    
    # Уведомляем вторую сторону
    from app.ws_manager import manager
    await manager.notify_user(req.target_username, {"system": "friend_removed", "from": current_user})
    
    return {"message": "Пользователь удален из друзей"}

@router.get("/requests", response_model=List[str])
async def get_incoming_requests(current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(Friendship.requester).where(
            and_(Friendship.addressee == current_user, Friendship.status == 'pending')
        )
    )
    return result.scalars().all()

@router.get("/list")
async def get_friends_list(current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(Friendship).where(
            and_(
                or_(Friendship.requester == current_user, Friendship.addressee == current_user),
                Friendship.status == 'accepted'
            )
        )
    )
    friendships = result.scalars().all()
    
    friends = []
    for f in friendships:
        if f.requester == current_user:
            friends.append(f.addressee)
        else:
            friends.append(f.requester)
            
    from app.ws_manager import manager
    return [{"username": f, "online": f in manager.active_connections} for f in friends]

@router.get("/suggestions", response_model=List[FriendSuggestion])
async def get_friend_suggestions(current_user: str = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    # 1. Находим всех, с кем уже есть любая связь (друзья или заявки)
    all_rel_query = select(Friendship).where(
        or_(Friendship.requester == current_user, Friendship.addressee == current_user)
    )
    all_rel_result = await session.execute(all_rel_query)
    related_users = {current_user}
    my_friends = set()
    
    for f in all_rel_result.scalars().all():
        other = f.addressee if f.requester == current_user else f.requester
        related_users.add(other)
        if f.status == 'accepted':
            my_friends.add(other)
    
    if not my_friends:
        return []

    # 2. Находим друзей наших друзей (второй круг)
    suggestions_query = select(Friendship).where(
        and_(
            or_(Friendship.requester.in_(my_friends), Friendship.addressee.in_(my_friends)),
            Friendship.status == 'accepted',
            ~Friendship.requester.in_(related_users),
            ~Friendship.addressee.in_(related_users)
        )
    )
    
    # SQLite не всегда оптимально переваривает NOT IN с большим списком, но для хобби-проекта ок.
    # Используем тильду (~) для инверсии в SQLAlchemy
    
    suggestions_result = await session.execute(suggestions_query)
    potential_friendships = suggestions_result.scalars().all()
    
    counts = {}
    for f in potential_friendships:
        p1, p2 = f.requester, f.addressee
        # Один из участников — наш друг, второй — кандидат
        candidate = p1 if p1 not in my_friends else p2
        
        # Дополнительная проверка на исключение
        if candidate not in related_users:
            counts[candidate] = counts.get(candidate, 0) + 1
            
    # 3. Сортируем и возвращаем топ-5
    sorted_suggestions = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return [FriendSuggestion(username=name, mutual_count=cnt) for name, cnt in sorted_suggestions]