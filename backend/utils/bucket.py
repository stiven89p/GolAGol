import os
import uuid
from typing import Optional
from fastapi import UploadFile
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv()

# Variables de entorno
SUPABASE_URL:str = os.getenv("SUPABASE_URL")
SUPABASE_KEY:str = os.getenv("SUPABASE_KEY")

# Entorno de bucket
env_bucket = os.getenv("SUPABASE_BUCKET")
if not env_bucket or env_bucket.startswith("ey"):
    SUPABASE_BUCKET = "imagenes"
else:
    SUPABASE_BUCKET = env_bucket

_supabase_client:Optional[Client] = None


# Funcion para obtener el cliente de Supabase
def getSupabaseClient():
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and API key are required.")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client

async def upload_file(file: UploadFile):
    client = getSupabaseClient()
    try:
        contenido = await file.read()
        # Generar nombre único con UUID
        extension = file.filename.split(".")[-1]
        nombre_unico = f"{uuid.uuid4()}.{extension}"
        pathArchivo = f"public/{nombre_unico}"
        
        result = client.storage.from_(SUPABASE_BUCKET).upload(
            path=pathArchivo,
            file=contenido,
            file_options={
                "content_type": file.content_type
            }
        )
        urlPublica = client.storage.from_(SUPABASE_BUCKET).get_public_url(pathArchivo)

        return urlPublica
    except Exception as e:
        print(f"DEBUG: Error uploading to Supabase: {e}")
        error_msg = str(e)
        if "403" in error_msg or "row-level security" in error_msg:
            raise Exception("Permiso denegado (RLS). Configura las políticas de tu bucket en Supabase para permitir 'INSERT'.")
        raise e
