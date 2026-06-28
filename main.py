from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL

import os
import re
import platform

app = FastAPI(
    title="Siempre Juntos API",
    version="1.0.0"
)

CARPETA_DESCARGAS = "descargas"

# Ruta de FFmpeg según el sistema operativo
if platform.system() == "Windows":
    FFMPEG_LOCATION = os.path.join(os.getcwd(), "ffmpeg", "bin")
else:
    FFMPEG_LOCATION = "/usr/bin"

os.makedirs(CARPETA_DESCARGAS, exist_ok=True)


class DescargarRequest(BaseModel):
    url: str


@app.get("/")
def inicio():
    return {
        "mensaje": "Servidor funcionando"
    }


@app.get("/health")
def health():
    return {
        "estado": "OK"
    }


@app.post("/info")
def obtener_info(datos: DescargarRequest):

    opciones = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True
    }

    try:

        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(datos.url, download=False)

        return {
            "titulo": info.get("title"),
            "canal": info.get("uploader"),
            "duracion": info.get("duration"),
            "miniatura": info.get("thumbnail")
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.post("/descargar")
def descargar(datos: DescargarRequest):

    try:

        # Obtener información del video
        with YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "noplaylist": True
        }) as ydl:

            info = ydl.extract_info(datos.url, download=False)

        titulo = info.get("title", "cancion")

        # Limpiar caracteres inválidos
        titulo = re.sub(r'[\\/*?:"<>|]', "", titulo)

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
            ydl.download([datos.url])

        archivo = os.path.join(
            CARPETA_DESCARGAS,
            titulo + ".mp3"
        )

        if not os.path.exists(archivo):
            raise HTTPException(
                status_code=500,
                detail="No se pudo generar el MP3."
            )

        return FileResponse(
            path=archivo,
            media_type="audio/mpeg",
            filename=f"{titulo}.mp3"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )