from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs

import os
import re
import platform

app = FastAPI(
    title="MP3 para Ti API",
    version="1.0.0"
)

CARPETA_DESCARGAS = "descargas"

if platform.system() == "Windows":
    FFMPEG_LOCATION = os.path.join(os.getcwd(), "ffmpeg", "bin")
else:
    FFMPEG_LOCATION = "/usr/bin"

os.makedirs(CARPETA_DESCARGAS, exist_ok=True)


class DescargarRequest(BaseModel):
    url: str


def limpiar_url_youtube(url: str) -> str:
    parsed = urlparse(url)

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.replace("/", "")
        return f"https://www.youtube.com/watch?v={video_id}"

    if "youtube.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        video_id = params.get("v")

        if video_id:
            return f"https://www.youtube.com/watch?v={video_id[0]}"

    return url


def limpiar_nombre_archivo(nombre: str) -> str:
    nombre = re.sub(r'[\\/*?:"<>|]', "", nombre)
    return nombre.strip() or "cancion_para_ti"


@app.get("/")
def inicio():
    return {
        "mensaje": "Servidor funcionando, amorcito"
    }


@app.get("/health")
def health():
    return {
        "estado": "OK",
        "mensaje": "Todo está listo para descargar música, amor"
    }


@app.post("/info")
def obtener_info(datos: DescargarRequest):

    if not datos.url.strip():
        raise HTTPException(
            status_code=400,
            detail="Amor, tienes que ingresar un enlace primero."
        )

    url_limpia = limpiar_url_youtube(datos.url)

    opciones = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True
    }

    try:
        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url_limpia, download=False)

        return {
            "titulo": info.get("title"),
            "canal": info.get("uploader"),
            "duracion": info.get("duration"),
            "miniatura": info.get("thumbnail")
        }

    except Exception as e:
        error = str(e)

        if "Sign in to confirm" in error:
            raise HTTPException(
                status_code=400,
                detail="Amor, YouTube bloqueó este enlace desde el servidor. Prueba con otro enlace."
            )

        raise HTTPException(
            status_code=400,
            detail="Amor, no pude obtener la información de esta canción. Intenta con otro enlace."
        )


@app.post("/descargar")
def descargar(datos: DescargarRequest):

    if not datos.url.strip():
        raise HTTPException(
            status_code=400,
            detail="Amor, tienes que ingresar un enlace primero."
        )

    try:
        url_limpia = limpiar_url_youtube(datos.url)

        with YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "noplaylist": True
        }) as ydl:
            info = ydl.extract_info(url_limpia, download=False)

        titulo = limpiar_nombre_archivo(info.get("title", "cancion_para_ti"))

        opciones = {
            "quiet": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "ffmpeg_location": FFMPEG_LOCATION,
            "outtmpl": os.path.join(
                CARPETA_DESCARGAS,
                titulo + ".%(ext)s"
            ),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        with YoutubeDL(opciones) as ydl:
            ydl.download([url_limpia])

        archivo = os.path.join(
            CARPETA_DESCARGAS,
            titulo + ".mp3"
        )

        if not os.path.exists(archivo):
            raise HTTPException(
                status_code=500,
                detail="Amor, no se pudo generar el MP3."
            )

        return FileResponse(
            path=archivo,
            media_type="audio/mpeg",
            filename=f"{titulo}.mp3"
        )

    except HTTPException:
        raise

    except Exception as e:
        error = str(e)

        if "Sign in to confirm" in error:
            raise HTTPException(
                status_code=400,
                detail="Amor, YouTube bloqueó este enlace desde el servidor. Prueba con otro enlace."
            )

        raise HTTPException(
            status_code=500,
            detail="Amor, ocurrió un problema al descargar la canción. Intenta con otro enlace."
        )