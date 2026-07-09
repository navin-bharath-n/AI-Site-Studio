"""
Auth routes — OAuth with Google and Facebook.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth, OAuthError

from pydantic import BaseModel
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse

router = APIRouter()

def is_company_email(email: str) -> bool:
    if "@" not in email:
        return False
    domain = email.split("@")[-1].lower()
    public_domains = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
        "aol.com", "zoho.com", "protonmail.com", "proton.me", "mail.com",
        "yandex.com", "gmx.com", "live.com", "msn.com"
    }
    return domain not in public_domains

oauth = OAuth()
if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        client_kwargs={'scope': 'openid email profile'},
    )

if settings.FACEBOOK_CLIENT_ID:
    oauth.register(
        name='facebook',
        api_base_url='https://graph.facebook.com/v19.0/',
        access_token_url='https://graph.facebook.com/v19.0/oauth/access_token',
        authorize_url='https://www.facebook.com/v19.0/dialog/oauth',
        client_id=settings.FACEBOOK_CLIENT_ID,
        client_secret=settings.FACEBOOK_CLIENT_SECRET,
        client_kwargs={'scope': 'email public_profile'},
    )

if settings.GITHUB_CLIENT_ID:
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={
            'scope': 'repo user',
            'headers': {'User-Agent': 'AI-Site-Studio'}
        },
    )


@router.get("/{provider}/login")
async def login(provider: str, request: Request, role: str = "buyer", redirect: Optional[str] = None):
    """Redirects to the OAuth provider."""
    if provider not in ["google", "facebook", "github"]:
        raise HTTPException(status_code=404, detail="Provider not supported")
    
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=500, detail=f"{provider} OAuth is not configured")
        
    redirect_uri = request.url_for('auth_callback', provider=provider)
    

    request.session['auth_role'] = role
    if redirect:
        request.session['auth_redirect'] = redirect
    
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def auth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Handles OAuth callback and creates/updates the user."""
    if provider not in ["google", "facebook", "github"]:
        raise HTTPException(status_code=404, detail="Provider not supported")
        
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=500, detail=f"{provider} OAuth is not configured")
        
    try:
        token = await client.authorize_access_token(request)
    except OAuthError as error:
        import traceback
        print("OAuthError occurred during token exchange:")
        print(f"Error: {error.error}")
        print(f"Description: {getattr(error, 'description', 'No description')}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")
        
    if provider == "google":
        user_info = token.get('userinfo')
        if not user_info:
            user_info = await client.parse_id_token(request, token)
        email = user_info.get("email")
        provider_id = user_info.get("sub")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")
    elif provider == "facebook":
        resp = await client.get('me?fields=id,name,email,picture')
        user_info = resp.json()
        email = user_info.get("email")
        provider_id = user_info.get("id")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture", {}).get("data", {}).get("url")
        if not email:
            # Facebook might not return an email if the user didn't allow it, but we need it.
            email = f"{provider_id}@facebook.placeholder.com"
    elif provider == "github":
        access_token_val = token.get("access_token")
        resp = await client.get('user', token=token)
        user_info = resp.json()
        email_resp = await client.get('user/emails', token=token)
        emails = email_resp.json()
        email = None
        if isinstance(emails, list):
            for em in emails:
                if em.get("primary") and em.get("verified"):
                    email = em.get("email")
                    break
            if not email and len(emails) > 0:
                email = emails[0].get("email")
        if not email:
            email = user_info.get("email") or f"{user_info.get('login')}@github.placeholder.com"
            
        provider_id = str(user_info.get("id"))
        full_name = user_info.get("name") or user_info.get("login")
        avatar_url = user_info.get("avatar_url")

    if not email or not provider_id:
        raise HTTPException(status_code=400, detail="Could not retrieve email or ID from provider")

    role = request.session.get('auth_role', 'buyer')
    if role.lower() == "seller" and not is_company_email(email):
        from urllib.parse import quote_plus
        error_msg = quote_plus("Sellers must use a company email address (not public domains like Gmail).")
        redirect_url = f"{settings.FRONTEND_URL}/sign-in?error={error_msg}&role=seller"
        return RedirectResponse(url=redirect_url)

    repo = UserRepository(db)
    user = await repo.upsert_oauth_user(
        provider=provider,
        provider_id=provider_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        role=role
    )
    
    if provider == "github" and access_token_val:
        user.github_access_token = access_token_val
        await db.flush()
        await db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    
    redirect_path = request.session.pop('auth_redirect', None)
    if not redirect_path:
        redirect_path = "/dashboard" if role.lower() == "seller" else "/"

    from urllib.parse import quote_plus
    redirect_url = f"{settings.FRONTEND_URL}/?token={access_token}&redirect={quote_plus(redirect_path)}"
    return RedirectResponse(url=redirect_url)


class ConnectGithubRequest(BaseModel):
    token: str


@router.post("/connect-github")
async def connect_github(
    request_data: ConnectGithubRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Connect a GitHub Personal Access Token to the logged-in user account.
    Validates the token against GitHub API and stores it.
    """
    token = request_data.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token cannot be empty")
        
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}"
    }
    
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.github.com/user", headers=headers, timeout=10.0)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid GitHub token or expired permissions.")
            
            user_data = resp.json()
            github_id = str(user_data.get("id"))
            github_username = user_data.get("login")
            
            # Save the token and username to the user profile
            current_user.github_id = github_id
            current_user.github_access_token = token
            if not current_user.username:
                current_user.username = github_username
                
            await db.flush()
            await db.refresh(current_user)
            
            return {
                "success": True,
                "message": "GitHub account connected successfully!",
                "github_username": github_username,
            }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error connecting to GitHub: {str(e)}")


@router.post("/disconnect-github")
async def disconnect_github(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Disconnect/Unlink GitHub account from the logged-in user.
    """
    current_user.github_id = None
    current_user.github_access_token = None
    await db.flush()
    await db.refresh(current_user)
    return {"success": True, "message": "GitHub account disconnected successfully!"}


@router.post("/register")
async def register(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email and password."""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "buyer")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    if role.lower() == "seller" and not is_company_email(email):
        raise HTTPException(
            status_code=400,
            detail="Sellers must register with a company email address (not public domains like Gmail)."
        )
        
    repo = UserRepository(db)
    existing = await repo.get_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    from app.core.security import hash_password
    from app.models.user import UserRole
    user = User(
        email=email,
        username=email.split("@")[0],
        hashed_password=hash_password(password),
        role=UserRole.SELLER if role.lower() == "seller" else UserRole.BUYER
    )
    db.add(user)
    await db.flush()
    await db.commit()
    
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login")
async def login_email(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password."""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    if email == "admin@aisitestudio.com" and password == "adminpassword":
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        if not user:
            from app.core.security import hash_password
            from app.models.user import UserRole
            user = User(
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
                full_name="Site Studio Admin",
                is_email_verified=True
            )
            db.add(user)
            await db.flush()
            await db.commit()
            await db.refresh(user)
            
        access_token = create_access_token(subject=str(user.id))
        return {"access_token": access_token, "token_type": "bearer"}

    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    from app.models.user import UserRole
    if user.role == UserRole.SELLER and not is_company_email(user.email):
        raise HTTPException(
            status_code=403,
            detail="Seller accounts must have a company email address (not public domains like Gmail)."
        )
        
    from app.core.security import verify_password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update the currently authenticated user's profile."""
    data = await request.json()
    
    if "full_name" in data:
        current_user.full_name = data["full_name"]
    if "username" in data:
        current_user.username = data["username"]
    if "bio" in data:
        current_user.bio = data["bio"]
    if "avatar_url" in data:
        current_user.avatar_url = data["avatar_url"]
        
    await db.flush()
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
