# --- START OF FILE main.py ---

import asyncio
import random
from logger import log
from config import (
    APP_ENABLE,
    LOOK_RESOURCE,
    LOOK_BUILDING,
    MINTIME,
    MAXTIME
)
from browser_utils import get_browser
from login import do_login
from gameworld import select_gameworld
from aldeias import get_villages
from recursos import upgrade_recursos
from construcoes import upgrade_construcoes

from fastapi import FastAPI, BackgroundTasks

# --- Configuração do FastAPI ---
app = FastAPI()

# Lock para garantir que apenas uma instância do bot seja executada por vez.
bot_lock = asyncio.Lock()

# --- Funções do Bot Refatoradas ---

async def process_single_village(page, aldeia):
    """
    Processa uma única aldeia usando uma página (aba) já existente.
    """
    log(f"Processando aldeia: {aldeia['nome']} (ID: {aldeia['id']})")
    try:
        # Navega para a aldeia específica usando o href dela
        await page.goto(aldeia['href'], {'waitUntil': 'networkidle0'})
        log(f"Navegação para a aldeia '{aldeia['nome']}' concluída.")

        if LOOK_RESOURCE:
            # A função upgrade_recursos já recebe o objeto 'page'
            await upgrade_recursos(page)
        
        if LOOK_BUILDING:
            # A função upgrade_construcoes já recebe o objeto 'page'
            await upgrade_construcoes(page)

        log(f"Processamento da aldeia '{aldeia['nome']}' finalizado com sucesso.")

    except Exception as e:
        log(f"Ocorreu um erro ao processar a aldeia '{aldeia['nome']}': {e}")
        # A exceção é registrada, mas o loop continua para a próxima aldeia

async def run_bot_session():
    """
    Orquestra uma sessão completa do bot:
    1. Abre o navegador
    2. Faz login UMA VEZ
    3. Itera por todas as aldeias
    4. Fecha o navegador no final
    """
    if not APP_ENABLE:
        log("Aplicativo está desabilitado nas configurações. Encerrando.")
        return

    browser = None
    log("Iniciando uma nova sessão do bot...")
    try:
        # Etapa 1: Iniciar navegador e fazer login
        browser = await get_browser()
        page = await browser.newPage()
        await page.goto('https://www.travian.com/', {'waitUntil': 'networkidle0'})

        await do_login(page)
        await select_gameworld(page)

        # Etapa 2: Obter a lista de aldeias para processar
        aldeias = await get_villages(page)
        if not aldeias:
            log("Nenhuma aldeia encontrada. Encerrando a sessão.")
            return

        log(f"Sessão iniciada. {len(aldeias)} aldeias a serem processadas: {[a['nome'] for a in aldeias]}")

        # Etapa 3: Iterar e processar cada aldeia na mesma sessão
        for aldeia in aldeias:
            await process_single_village(page, aldeia)
            
            # Pausa aleatória entre o processamento de aldeias
            tempo_espera = random.randint(MINTIME, MAXTIME)
            log(f"Pausa de {tempo_espera} segundos antes da próxima tarefa.")
            await asyncio.sleep(tempo_espera)
        
        log("Ciclo completo de todas as aldeias finalizado.")

    except Exception as e:
        log(f"Erro fatal na sessão principal do bot: {e}")
    finally:
        # Etapa 4: Garantir que o navegador seja fechado no final ou em caso de erro
        if browser:
            await browser.close()
            log("Sessão do bot encerrada e navegador fechado. Recursos liberados.")

# --- Endpoints da API ---

@app.get("/")
async def root():
    return {"message": "Servidor do Bot Travian está no ar."}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/run")
async def run_bot_endpoint(background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar a sessão do bot em segundo plano.
    Usa um lock para evitar execuções concorrentes.
    """
    if bot_lock.locked():
        log("Tentativa de iniciar o bot, mas uma sessão já está em execução.")
        return {"status": "error", "message": "O bot já está em execução."}

    async with bot_lock:
        log("Endpoint /run acionado. Adicionando a sessão do bot à fila de tarefas em segundo plano.")
        background_tasks.add_task(run_bot_session)
    
    return {"status": "success", "message": "A sessão do bot foi iniciada em segundo plano."}

# --- Para testes locais (opcional) ---
if __name__ == "__main__":
    log("Executando o bot diretamente via script para uma sessão completa.")
    asyncio.run(run_bot_session())