import os
import nest_asyncio
import glob
import time
import requests
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

# Guardar ARL en el config de deemix (usando directorio local)
config_dir = os.path.expanduser("~/.config/deemix")
os.makedirs(config_dir, exist_ok=True)
with open(os.path.join(config_dir, "arl"), "w") as f:
    f.write(ARL)

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

    # Ejecutar deemix con ARL
    os.system(f"deemix -p {DOWNLOAD_DIR} https://www.deezer.com/track/{track_id} > /dev/null 2>&1")

    # Esperar hasta 40s a que aparezca el archivo
    for _ in range(40):
        archivos = glob.glob(f"{DOWNLOAD_DIR}/**/*.*", recursive=True)
        archivos = [f for f in archivos if f.lower().endswith((".mp3", ".flac"))]
        if archivos:
            return archivos[0]
        time.sleep(1)
    return None

# 📌 Menú principal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Buscar Canción 🎵", callback_data="buscar_cancion")],
        [InlineKeyboardButton("Buscar Artista 👩‍🎤", callback_data="buscar_artista")],
        [InlineKeyboardButton("Buscar Álbum 💿", callback_data="buscar_album")],
    ]
    await update.message.reply_text("👋 Hola, elige una opción:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        return await update.message.reply_text("⚠️ No se encontraron resultados. Intenta de nuevo.")

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
        return await start(update, context)

    if data.startswith("track_"):
        track_id = data.split("_")[1]
        await query.message.reply_text("⏳ Descargando... por favor espera...")
        archivo = descargar_track(track_id)
        if archivo:
            try:
                with open(archivo, "rb") as audio_file:
                    await query.message.reply_audio(audio_file)
            except Exception as e:
                await query.message.reply_text(f"⚠️ Error al enviar el archivo: {str(e)}")
        else:
            await query.message.reply_text("⚠️ No se pudo descargar el archivo. Intenta de nuevo.")

# 📌 Registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(menu_callback, pattern="^buscar_"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buscar))
application.add_handler(CallbackQueryHandler(elegir, pattern="^(track_|volver)"))

# 📌 Iniciar bot
if __name__ == "__main__":
    print("🤖 Bot iniciando...")
    application.run_polling()