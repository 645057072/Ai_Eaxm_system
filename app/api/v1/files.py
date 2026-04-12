# -*- coding: utf-8 -*-
"""上传文件下载（需管理员）。"""

import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import require_roles
from app.core.config import get_settings
from app.models.user import User

router = APIRouter()

_FILENAME_SAFE = re.compile(r"^ent_\d+_[a-f0-9]{32}\.[A-Za-z0-9]+$")


@router.get("/{filename}")
def download_file(
    filename: str,
    _: Annotated[User, Depends(require_roles("admin"))],
) -> FileResponse:
    if not _FILENAME_SAFE.match(filename):
        raise HTTPException(status_code=404, detail="文件不存在")
    root = Path(get_settings().upload_root)
    path = root / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path, filename=filename, media_type="application/octet-stream")
