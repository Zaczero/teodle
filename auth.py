import secrets

from fastapi import Request, status
from fastapi.responses import FileResponse

from config import PASSWORD


async def auth_middleware(request: Request, call_next):
    if PASSWORD is None:
        return await call_next(request)

    if request.url.path.startswith('/userscript/ws'):
        return await call_next(request)

    auth_value = request.cookies.get('auth', '')

    if secrets.compare_digest(auth_value, PASSWORD):
        return await call_next(request)

    return FileResponse('html/auth.html', status_code=status.HTTP_401_UNAUTHORIZED)
