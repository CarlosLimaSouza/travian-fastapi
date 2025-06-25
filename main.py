import os
import asyncio
import psutil
from browser_utils import get_browser
from login import do_login
from lobby import go_to_lobby
from gameworld import select_gameworld
from recursos import upgrade_recursos
from construcoes import upgrade_construcoes
from logger import log
from config import LOOK_RESOURCE, LOOK_BUILDING,APP_ENABLE
from aldeias import get_villages
import gc
from fastapi import FastAPI , BackgroundTasks

def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024  # in MB
    log(f"Memory usage: {mem:.2f} MB")

app = FastAPI()

from fastapi import BackgroundTasks


@app.post("/send/")
async def send_notification(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "Notification sent")
    return {"message": "Task is running in background"}

@app.get("/run")
async def run_endpoint():
    asyncio.create_task(main())
    return {"message": "Started main() in background"}

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/ping")
async def ping():
    print("[DEBUG] /ping chamado")
    return {"status": "ok"}


        


async def main():
    browser = None
    try:
        browser = await get_browser()
        page = await browser.newPage()
        await page.goto('https://www.travian.com/')
        log_memory_usage()

        if APP_ENABLE:
            log("Aplicativo está habilitado. Iniciando o processo...") 
        else:
            log("Aplicativo está desabilitado. Encerrando o processo.")
            return

        await do_login(page)
        log_memory_usage()
        await select_gameworld(page)
        log_memory_usage()
        gc.collect()
        aldeias = await get_villages(page)
        log_memory_usage()
        if not aldeias:
            log('Nenhuma aldeia encontrada. Encerrando o processo.')
            return
        log(f'aldeias encontradas: {aldeias}')
        
        for aldeia in aldeias:
            # await page.close()
            # page = await browser.newPage()
            gc.collect()

            log(f'Processando aldeia: {aldeia["nome"]} (ID: {aldeia["id"]})')
            await page.goto(aldeia['href'], waitUntil='networkidle0')
            if LOOK_RESOURCE:
                await upgrade_recursos(page)    
            if LOOK_BUILDING: 
                await upgrade_construcoes(page)
            log_memory_usage()
    except Exception as e:
        log(f"Erro no main: {e}")
    finally:
        if browser:
            await browser.close()  # Fecha o navegador ao final

# Função para rodar o main async em thread separada
# asyncio.run(main())

@app.get("/teste")
async def teste_endpoint():
    from pyppeteer import launch
    browser = None
    try:
        browser = await launch(
            executablePath="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        page = await browser.newPage()
        await page.goto("https://www.google.com/")
        log("[TESTE] Google carregado com sucesso!")
        return {"status": "ok", "message": "Google carregado com sucesso!"}
    except Exception as e:
        log(f"[TESTE] Erro ao abrir Google: {e}")
        return {"status": "erro", "detail": str(e)}
    finally:
        if browser:
            await browser.close()






