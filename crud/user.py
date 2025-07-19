from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User


async def add_user(session: AsyncSession, id: int, username: str, full_name: str) -> bool:
    existing_user = await session.scalar(select(User).where(User.id == id))

    if existing_user is None:
        user = User(
            id=id,
            username=username,
            full_name=full_name
        )
        session.add(user)
        await session.commit()
        return True
    else:
        return False


