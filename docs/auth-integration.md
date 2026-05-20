# Интеграция аутентификации в микросервисы

> **Куда идти за правдой:** `services/auth/app/core/security.py` — JWT-подпись, `services/auth/app/api/v1/routers/auth.py` — `get_current_user`.

---

## 1. Принцип

Каждый микросервис (`content`, `assessment`, и будущие) **самостоятельно** валидирует JWT, который приходит в заголовке `Authorization: Bearer <token>`. Никаких сетевых запросов к `auth` в рантайме — только общий `SECRET_KEY`, общий Redis и общая схема токена.

---

## 2. Что содержит access-токен (payload)

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "access",
  "role": "methodist",
  "jti": "uuid4",
  "exp": 1716232222
}
```

| Поле | Описание |
|------|----------|
| `sub` | UUID пользователя (строка) |
| `type` | `"access"` или `"refresh"` |
| `role` | `admin` / `methodist` / `seminarist` / `candidate` |
| `jti` | Уникальный идентификатор токена (UUID4), для blacklist |
| `exp` | Unix-timestamp истечения |

---

## 3. Файлы, которые нужно создать в новом микросервисе

### 3.1 `app/core/config.py`

```python
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=str(_ROOT_DIR / ".env"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 3.2 `app/core/redis.py`

**Копируй идентично** из `services/auth/app/core/redis.py`:

```python
import asyncio
from contextlib import suppress

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()
_redis_pool: Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


async def get_redis_pool() -> Redis:
    global _redis_pool, _redis_loop
    current_loop = asyncio.get_running_loop()
    if _redis_pool is None or _redis_loop != current_loop:
        if _redis_pool is not None:
            with suppress(RuntimeError):
                await _redis_pool.aclose()
        _redis_pool = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_loop = current_loop
    return _redis_pool


async def close_redis_pool() -> None:
    global _redis_pool, _redis_loop
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        _redis_loop = None
```

### 3.3 `app/core/security.py`

Только `decode_token` (создание токенов — прерогатива `auth`):

```python
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

### 3.4 `app/api/deps.py` (или `app/dependencies.py`)

Главная зависимость для защиты эндпоинтов:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis_pool
from app.core.security import decode_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis_pool),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        if is_blacklisted:
            raise credentials_exception

    user_id = payload.get("sub")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {
        "id": user_id,
        "role": role,
    }
```

### 3.5 `app/core/permissions.py`

```python
from collections.abc import Sequence

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user


async def require_role(allowed_roles: Sequence[str]):
    async def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return checker


require_admin = require_role(["admin"])
require_manager_or_admin = require_role(["admin", "methodist"])
```

### 3.6 `app/main.py` — lifespan

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.redis import close_redis_pool


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_redis_pool()


app = FastAPI(title="KMS Content Service", lifespan=lifespan)
```

---

## 4. Пример защиты эндпоинта

```python
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.post("/modules")
async def create_module(user: dict = Depends(require_role(["admin", "methodist"]))):
    # user = {"id": "550e8400-...", "role": "methodist"}
    ...


@router.get("/modules/{module_id}")
async def get_module(module_id: int, user: dict = Depends(get_current_user)):
    # Любой авторизованный пользователь
    ...
```

---

## 5. Тестирование

В `conftest.py` создавай `AsyncClient` с токеном:

```python
import pytest
from httpx import AsyncClient


@pytest.fixture
async def client():
    # ... инициализация app, db ...
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def get_auth_token(client: AsyncClient) -> str:
    """Получить токен через login auth-сервиса (или сгенерировать в тесте)."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    return response.json()["access_token"]
```

---

## 6. Частые ошибки

| Ошибка | Причина |
|--------|---------|
| `401` всегда | `SECRET_KEY` или `ALGORITHM` не совпадает с `auth` |
| `401` после logout | Забыли проверять `blacklist:{jti}` в Redis |
| `401` при рефреше | Пытаешься использовать access-токен как refresh |
| `403` для admin | В `require_role` передал роль, которой нет в токене |

---

## 7. Безопасность роли в JWT

**Проблема:** если роль пользователя изменится (например, `candidate` → `methodist`), старые access-токены всё ещё содержат старую роль. Access-токен живёт **30 минут**, поэтому окно несоответствия ограничено.

**Меры:**
- Access-токен короткоживущий (30 мин).
- При критичных операциях (удаление, смена прав) можно добавлять дополнительную проверку через БД auth-сервиса — но в нашем проекте это избыточно.
- Refresh-токен (7 дней) **не содержит роли** — это нормально, он только для обновления access.
