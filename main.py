import os
import nest_asyncio
import glob
import time
import requests
import json
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ✅ Configura aquí - Usando variables de entorno para seguridad
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ARL = os.getenv("DEEZER_ARL", "")

if not TOKEN:
    print("⚠️ ERROR: TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")
    exit(1)

if not ARL:
    print("⚠️ ERROR: DEEZER_ARL no está configurado en las variables de entorno")
    exit(1)

# Carpeta de descargas
DOWNLOAD_DIR = "deezer_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configurar deemix con ARL
config_dir = os.path.expanduser("~/.config/deemix")
os.makedirs(config_dir, exist_ok=True)

# Configuración básica de deemix con ARL
config_content = {
    "arl": ARL,
    "downloadLocation": DOWNLOAD_DIR,
    "maxBitrate": "9",
    "fallbackBitrate": True,
    "createArtistFolder": True,
    "createAlbumFolder": False,
    "createCDFolder": False,
    "padTracks": True,
    "paddingSize": "0",
    "illegalCharacterReplacer": "_",
    "queueConcurrency": 3,
    "overwriteFile": "y",
    "saveArtwork": True,
    "tracknameTemplate": "%artist% - %title%",
    "albumTracknameTemplate": "%tracknumber% - %title%"
}

with open(os.path.join(config_dir, "config.json"), "w") as f:
    json.dump(config_content, f, indent=2)

# Aplicación de Telegram
nest_asyncio.apply()
application = ApplicationBuilder().token(TOKEN).build()

HEADERS = {"User-Agent": "Mozilla/5.0"}

def buscar_cancion(query):
    url = f"https://api.deezer.com/search/track?q={query}&index=0&limit=10"
    res = requests.get(url, headers=HEADERS).json()
    return res.get("data", [])

def buscar_artista(query):
    url = f"https://api.deezer.com/search/artist?q={query}&index=0&limit=1"
    res = requests.get(url, headers=HEADERS).json()
    artistas = res.get("data", [])
    if not artistas:
        return []
    artist_id = artistas[0]["id"]
    url = f"https://api.deezer.com/artist/{artist_id}/top?limit=10"
    res = requests.get(url, headers=HEADERS).json()
    return res.get("data", [])

def buscar_album(query):
    url = f"https://api.deezer.com/search/album?q={query}&index=0&limit=1"
    res = requests.get(url, headers=HEADERS).json()
    albums = res.get("data", [])
    if not albums:
        return []
    album_id = albums[0]["id"]
    url = f"https://api.deezer.com/album/{album_id}/tracks"
    res = requests.get(url, headers=HEADERS).json()
    return res.get("data", [])

def descargar_track(track_id):
    # Borrar descargas anteriores
    for f in glob.glob(f"{DOWNLOAD_DIR}/**/*.*", recursive=True):
        try:
            os.remove(f)
        except:
            pass

    # Ejecutar deemix con ARL enviado por stdin
    try:
        # Validar que track_id sea numérico para seguridad
        if not track_id.isdigit():
            return None
            
        cmd = ["deemix", "-p", DOWNLOAD_DIR, f"https://www.deezer.com/track/{track_id}"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=ARL, timeout=120)
        
        # Buscar archivo descargado
        archivos = glob.glob(f"{DOWNLOAD_DIR}/**/*.*", recursive=True)
        archivos = [f for f in archivos if f.lower().endswith((".mp3", ".flac"))]
        if archivos:
            return archivos[0]
    except Exception as e:
        print(f"Error en descarga: {e}")
    
    return None

# 📌 Función para obtener información de una canción
def obtener_info_cancion(track_id):
    try:
        url = f"https://api.deezer.com/track/{track_id}"
        res = requests.get(url, headers=HEADERS).json()
        return res
    except:
        return None

# 📌 Mostrar menú principal
async def mostrar_menu(chat, text="👋 Hola, elige una opción:"):
    keyboard = [
        [InlineKeyboardButton("Buscar Canción 🎵", callback_data="buscar_cancion")],
        [InlineKeyboardButton("Buscar Artista 👩‍🎤", callback_data="buscar_artista")],
        [InlineKeyboardButton("Buscar Álbum 💿", callback_data="buscar_album")],
    ]
    await chat.send_message(text, reply_markup=InlineKeyboardMarkup(keyboard))

# 📌 Menú principal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Manejar tanto mensajes directos como callback queries
    if update.message:
        chat = update.message.chat
    elif update.callback_query:
        chat = update.callback_query.message.chat
    else:
        return
    
    await mostrar_menu(chat)

# 📌 Callback de menú
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    opcion = query.data

    if opcion == "buscar_cancion":
        context.user_data["modo"] = "cancion"
        await query.message.reply_text("🎵 Escribe el nombre de la canción que quieres buscar:")
    elif opcion == "buscar_artista":
        context.user_data["modo"] = "artista"
        await query.message.reply_text("👩‍🎤 Escribe el nombre del artista que quieres buscar:")
    elif opcion == "buscar_album":
        context.user_data["modo"] = "album"
        await query.message.reply_text("💿 Escribe el nombre del álbum que quieres buscar:")

# 📌 Mensaje de texto según el modo
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    modo = context.user_data.get("modo") if context.user_data else None
    query = update.message.text.strip() if update.message.text else ""
    resultados = []

    if modo == "cancion":
        resultados = buscar_cancion(query)
    elif modo == "artista":
        resultados = buscar_artista(query)
    elif modo == "album":
        resultados = buscar_album(query)

    if not resultados:
        await update.message.reply_text("⚠️ No se encontraron resultados. Intenta de nuevo.")
        await mostrar_menu(update.message.chat, "❌ Sin resultados. ¿Quieres buscar algo más?")
        return

    keyboard = []
    for i, track in enumerate(resultados[:10], 1):
        title = track.get("title", track.get("name", ""))
        artist = track["artist"]["name"] if "artist" in track else ""
        keyboard.append([InlineKeyboardButton(f"{i}. {title} - {artist}", callback_data=f"track_{track['id']}")])

    keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="volver")])

    await update.message.reply_text(
        f"🔎 Resultados para *{query}*: ",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📌 Elegir resultado
async def elegir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "volver":
        await start(update, context)
        return

    if data.startswith("track_"):
        track_id = data.split("_")[1]
        await query.message.reply_text("⏳ Descargando... por favor espera...")
        
        # Obtener información de la canción
        info_cancion = obtener_info_cancion(track_id)
        
        archivo = descargar_track(track_id)
        if archivo:
            try:
                # Preparar mensaje con información de la canción
                if info_cancion:
                    titulo = info_cancion.get('title', 'Desconocido')
                    artista = info_cancion.get('artist', {}).get('name', 'Desconocido')
                    album = info_cancion.get('album', {}).get('title', 'Desconocido')
                    duracion = info_cancion.get('duration', 0)
                    minutos = duracion // 60
                    segundos = duracion % 60
                    
                    mensaje_info = f"🎵 **{titulo}**\n👩‍🎤 Artista: {artista}\n💿 Álbum: {album}\n⏱️ Duración: {minutos}:{segundos:02d}"
                else:
                    mensaje_info = "🎵 Canción descargada"
                
                with open(archivo, "rb") as audio_file:
                    await query.message.reply_audio(
                        audio_file, 
                        caption=mensaje_info, 
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                # Mostrar menú después de la descarga
                await mostrar_menu(query.message.chat, "✅ ¡Descarga completada! ¿Qué más quieres hacer?")
                
            except Exception as e:
                await query.message.reply_text(f"⚠️ Error al enviar el archivo: {str(e)}")
                await mostrar_menu(query.message.chat, "⚠️ Hubo un error. ¿Quieres intentar otra cosa?")
        else:
            await query.message.reply_text("⚠️ No se pudo descargar el archivo. Intenta de nuevo.")
            await mostrar_menu(query.message.chat, "⚠️ No se pudo descargar. ¿Quieres intentar otra cosa?")

# 📌 Registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(menu_callback, pattern="^buscar_"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buscar))
application.add_handler(CallbackQueryHandler(elegir, pattern="^(track_|volver)"))

# 📌 Iniciar bot
if __name__ == "__main__":
    print("🤖 Bot iniciando...")
    application.run_polling()
    