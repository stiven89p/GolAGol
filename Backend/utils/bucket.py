import os
import uuid
from pathlib import Path
from fastapi import UploadFile
STORE_DIR = "bucket"

Path(STORE_DIR).mkdir(parents=True, exist_ok=True)

async def upload_file(file: UploadFile):
    content = await file.read()
    org_name = file.filename
    new_file_name = f"{uuid.uuid4().hex}_{org_name}"
    file_path = os.path.join(STORE_DIR, new_file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    return {
        "file_name": new_file_name,
        "original_name": org_name
    }
