import random
import asyncio
from config import MINTIME, MAXTIME, TEST_MODE
from logger import log
from recursos_config import valida_upgrade,converte_gid_para_nome
from browser_utils import get_browser

async def upgrade_recursos(page):
    log('Verificando recursos...')
    await page.click('#navigation a.resourceView')
    await page.waitForSelector('#resourceFieldContainer', timeout=40000)

    # Obtém a lista de recursos disponíveis para upgrade
    lista_recursos = await page.evaluate('''
        () => {
            const container = document.getElementById('resourceFieldContainer');
            if (!container) return [];
            const links = container.querySelectorAll('a.good');
            return Array.from(links).map(link => ({
                id: link.getAttribute('data-aid'),
                gid: link.getAttribute('data-gid'),
                level: link.querySelector('div.labelLayer').textContent.trim(),
                href: link.href
            }));
        }
    ''')
    if not lista_recursos:
        log('Nenhum recurso disponível para upgrade.')
        return
    # log(f'Recursos disponíveis para upgrade: {lista_recursos}')

    
    # valida os upgrades possíveis
    recursos_validos = [r for r in lista_recursos if valida_upgrade(r['gid'], r['level'])]
    if not recursos_validos:
        log('Nenhum recurso válido para upgrade.')
        return
    # log(f'Recursos válidos para upgrade: {recursos_validos}')
    recurso_clicado = False
    for recurso in recursos_validos:
        try:
            log(f"URL da contrução: {recurso['href']}")
            if page.isClosed():
                log("Pagina estava fechada. abrindo nova...")
                page = await browser.newPage()
            try:
                await page.goto(recurso['href'], waitUntil='networkidle0', timeout=25000)
                recurso_clicado = True
            except Exception as e:
                log(f"Unexpected error: {e}")
            log(f'Recurso {converte_gid_para_nome(recurso["gid"])} clicado para upgrade..o nível atual é {recurso["level"]}.')
            break  # Sai do loop após clicar no primeiro recurso válido
        except Exception as e:
            log(f'Erro ao clicar no recurso ID:{recurso["id"]}/campo_{converte_gid_para_nome(recurso["gid"])}: {e}') 

    if not recurso_clicado:
        log('Nenhum recurso válido encontrado para upgrade.')
        return

    if recurso_clicado:
        # Espera o botão de upgrade aparecer
        await page.waitForSelector('.upgradeButtonsContainer', timeout=30000)
        if TEST_MODE:
            log('[TESTE] Botão de upgrade de recurso seria clicado agora!')
        else:
            await page.click('.upgradeButtonsContainer .section1 button.build')
            log('Botão de upgrade de recurso clicado!')
    else:
        log('falha ao clicar no recurso para upgrade.')

    await asyncio.sleep(random.randint(MINTIME, MAXTIME))