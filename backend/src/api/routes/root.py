"""Root route for serving the demo UI."""
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from src.api.auth import generate_jwt
from src.api.middleware import require_basic_auth
from src.core.config import AuthConfig

router = APIRouter()

# Cache the index.html template at module load
_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "index.html"
_INDEX_HTML_TEMPLATE = _TEMPLATE_PATH.read_text()


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for load balancers and monitoring."""
    return JSONResponse(content={"status": "healthy"})


@router.get("/")
async def root(auth_config: AuthConfig = Depends(require_basic_auth)) -> HTMLResponse:
    """Serve the demo UI with an embedded JWT token.
    
    Requires HTTP Basic Authentication. The browser will prompt for
    username and password. Upon successful authentication, a JWT token
    is generated and embedded into the HTML response for use by the
    frontend JavaScript.
    """
    token = generate_jwt(auth_config.app_key)
    html_content = _INDEX_HTML_TEMPLATE.replace("[TOKEN]", token)
    return HTMLResponse(content=html_content)
