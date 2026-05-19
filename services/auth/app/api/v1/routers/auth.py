from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models import Invitation, Role, User
from app.db.session import get_db
from app.schemas import RegisterWithInvitation, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_redis():
    """Yield a Redis connection for dependency injection."""
    redis = Redis.from_url(settings.REDIS_URL)
    try:
        yield redis
    finally:
        await redis.aclose()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    """Validate token and return the current authenticated user."""
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
    if user_id is None:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterWithInvitation, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user with email and password.

    First user becomes admin automatically.
    All subsequent users require a valid invitation token.
    """
    # Check duplicate email first
    result = await db.execute(
        select(User).where(User.email == user_data.email).options(selectinload(User.roles))
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Check if this is the first user
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar()
    is_first_user = user_count == 0

    invitation: Invitation | None = None
    if not is_first_user:
        # Require invitation token
        if not user_data.invitation_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation token required"
            )

        result = await db.execute(
            select(Invitation).where(Invitation.token == user_data.invitation_token)
        )
        invitation = result.scalar_one_or_none()
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation token"
            )
        if invitation.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already used"
            )
        if invitation.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired"
            )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email, hashed_password=hashed_password, full_name=user_data.full_name
    )

    if is_first_user:
        # First user gets admin role
        role_result = await db.execute(select(Role).where(Role.name == UserRole.ADMIN))
        admin_role = role_result.scalar_one()
        new_user.roles.append(admin_role)
    else:
        assert invitation is not None
        # Assign role from invitation
        role_result = await db.execute(select(Role).where(Role.id == invitation.role_id))
        role = role_result.scalar_one()
        new_user.roles.append(role)
        new_user.manager_id = invitation.manager_id
        new_user.invited_by = invitation.created_by

        # Mark invitation as used
        invitation.used = True
        invitation.used_by = new_user.id

    db.add(new_user)
    await db.commit()

    result = await db.execute(
        select(User).where(User.id == new_user.id).options(selectinload(User.roles))
    )
    return result.scalar_one()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Token:
    """Authenticate user and return access and refresh tokens."""
    # Rate limiting: 5 attempts per minute per IP
    client_ip = "127.0.0.1"  # In production, get from request headers
    rate_key = f"rate_limit:login:{client_ip}"
    attempts = await redis.get(rate_key)
    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        await redis.incr(rate_key)
        await redis.expire(rate_key, 60)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await redis.delete(rate_key)
    access_token = create_access_token(data={"sub": str(user.id), "jti": str(uuid4())})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": str(uuid4())})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme), redis: Redis = Depends(get_redis)
) -> dict[str, str]:
    """Invalidate the current access token by adding it to the blacklist."""
    payload = decode_token(token)
    if payload and payload.get("jti"):
        jti = payload["jti"]
        exp = payload.get("exp")
        if exp:
            ttl = int(exp) - int(datetime.now(UTC).timestamp())
            if ttl > 0:
                await redis.setex(f"blacklist:{jti}", ttl, "true")

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> Token:
    """Refresh access token using a valid refresh token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked"
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id), "jti": str(uuid4())})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": str(uuid4())})

    return Token(access_token=access_token, refresh_token=new_refresh_token)
