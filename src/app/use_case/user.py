from app.entities.user import UserCreateDTO, UserUpdateDTO
from app.repositories.user import UserRepository


class UserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository: UserRepository = user_repository

    async def user_init(self, user_id: int, name: str):
        """
        Возвращает существующего пользователя или создаёт нового.
        user_id — внешний идентификатор (например, Telegram user_id → max_id).
        name    — username пользователя.
        """
        user = await self._user_repository.get_by_id(user_id)

        if user is None:
            dto = UserCreateDTO(
                max_id=user_id,
                username=name,
                phone=None,
                options=None,
            )
            user = await self._user_repository.create(dto)
        elif user.username != name:
            # Обновляем имя, если оно изменилось
            user = (
                await self._user_repository.update(
                    user_id, UserUpdateDTO(username=name)
                )
                or user
            )

        return user
