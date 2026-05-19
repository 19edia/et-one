import logging
import os
import asyncio
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Configurar o logging para monitorar o comportamento do sistema
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente de um arquivo .env (útil para testes locais)
load_dotenv()

# --- Lógica Central do Jogo ---
# Esta função centraliza as respostas para que o Telegram e o Site usem a mesma lógica.
def get_game_response(text: str, user_name: str) -> str:
    text = text.lower().strip()
    
    if text == "/start":
        return f"Olá, {user_name}! Bem-vindo ao nosso MMORPG de texto. Use /help para ver os comandos disponíveis."
    elif text == "/ping":
        return "Pong! 🏓 O servidor está rodando perfeitamente tanto na Web quanto no Telegram."
    elif text == "/help":
        return "<b>Comandos Disponíveis:</b>\n/start - Inicia a jornada\n/help - Mostra esta mensagem\n/ping - Verifica conexão"
    
    return f"Você disse: '{text}'. Por enquanto, eu ainda estou aprendendo as artes do combate!"

# --- Handlers do Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /start é emitido."""
    response = get_game_response("/start", update.effective_user.first_name)
    await update.message.reply_html(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista os comandos disponíveis."""
    response = get_game_response("/help", "")
    await update.message.reply_html(response)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verifica se o bot está online."""
    response = get_game_response("/ping", "")
    await update.message.reply_text(response)

# --- Configuração do Bot e Servidor Web ---
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    raise ValueError("A variável de ambiente TELEGRAM_TOKEN não foi encontrada!")

application = Application.builder().token(token).build()

# Registra os handlers de comando no Telegram
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("ping", ping))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o bot do Telegram em background
    await application.initialize()
    await application.start()
    if application.updater:
        await application.updater.start_polling()
    
    logger.info("Sistema iniciado: Bot Telegram (Polling) + Servidor Web FastAPI.")
    yield
    # Desliga o bot ao fechar o servidor
    if application.updater:
        await application.updater.stop()
    await application.stop()
    await application.shutdown()

web_app = FastAPI(lifespan=lifespan)

# Rota principal para carregar a interface HTML
@web_app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Arquivo index.html não encontrado!</h1>"

    # O Render define automaticamente a porta através da variável de ambiente PORT
    port = int(os.getenv("PORT", 8000))
    
    # Inicia o servidor Uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=port)