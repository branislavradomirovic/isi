from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

ROUTER_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROUTER_DIR / "templates"))
router = APIRouter()


@router.get("/", include_in_schema=False)
def public_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Institut za socijalnu inkluziju"},
    )
