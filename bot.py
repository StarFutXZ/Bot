import discord
from discord.ext import tasks, commands
import aiohttp
import os
import asyncio
from aiohttp import web
from datetime import datetime
from zoneinfo import ZoneInfo

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

id_ultima_mensagem = None
ultimo_corpo_texto = ""
tempo_ultima_verificacao = None
CANAL_ID = 1542669778999574599  # ID do teu canal

def calcular_tempo_relativo():
    if not tempo_ultima_verificacao:
        return "há poucos segundos"
    
    agora = datetime.now(ZoneInfo("Europe/Lisbon"))
    diferenca = int((agora - tempo_ultima_verificacao).total_seconds())
    
    if diferenca < 10:
        return "há poucos segundos"
    elif diferenca < 60:
        return f"há {diferenca} segundos"
    elif diferenca < 3600:
        minutos = diferenca // 60
        return f"há {minutos} minuto" if minutos == 1 else f"há {minutos} minutos"
    else:
        horas = diferenca // 3600
        return f"há {horas} hora" if horas == 1 else f"há {horas} horas"

def construir_payload(corpo_texto):
    tempo_relativo = calcular_tempo_relativo()
    footer_texto = f"Auto-updated. Last check: {tempo_relativo}"
    
    return {
        "flags": 32768,
        "components": [
            {
                "type": 17,  # Container
                "components": [
                    {
                        "type": 12,  # Media Gallery com a imagem do topo
                        "items": [
                            {
                                "media": {
                                    "url": "https://cdn.discordapp.com/attachments/1379466761354874954/1547849387290656828/real-status.png"
                                }
                            }
                        ]
                    },
                    {
                        "type": 14,  # Divisor
                        "divider": True,
                        "spacing": 1
                    },
                    {
                        "type": 10,
                        "content": corpo_texto
                    },
                    {
                        "type": 14,  # Divisor
                        "divider": True,
                        "spacing": 1
                    },
                    {
                        "type": 10,
                        "content": f"-# {footer_texto}"
                    }
                ]
            }
        ]
    }

@bot.event
async def on_ready():
    global id_ultima_mensagem, tempo_ultima_verificacao
    print(f"Bot ligado com sucesso como {bot.user}")
    
    tempo_ultima_verificacao = datetime.now(ZoneInfo("Europe/Lisbon"))
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
        async for mensagem in canal.history(limit=20):
            if mensagem.author.id == bot.user.id:
                id_ultima_mensagem = mensagem.id
                print(f"Mensagem anterior detetada (ID: {id_ultima_mensagem}).")
                break
    except Exception as e:
        print(f"Erro ao procurar mensagem anterior: {e}")

    if not sincronizar_api.is_running():
        sincronizar_api.start()
        print("Loop principal da API (15 min) iniciado!")
        
    if not atualizar_tempo_ui.is_running():
        atualizar_tempo_ui.start()
        print("Loop de atualização visual do tempo (1 min) iniciado!")

@tasks.loop(minutes=15)
async def sincronizar_api():
    global ultimo_corpo_texto, tempo_ultima_verificacao, id_ultima_mensagem
    
    try:
        print("A verificar atualizações da API WEAO...")
        url = "https://weao.xyz/api/status/exploits"
        headers = {"User-Agent": "WEAO-3PService"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    dados = await response.json()
                    tempo_ultima_verificacao = datetime.now(ZoneInfo("Europe/Lisbon"))
                    
                    windows_exploits = []
                    mac_exploits = []
                    windows_externals = []
                    
                    nomes_externals_conhecidos = [
                        "serotonin", "matcha", "severe", "lumen", "matrix hub", 
                        "melatonin", "axis", "photon", "ronin", "dx9ware v2", "dx9ware"
                    ]
                    
                    if isinstance(dados, list):
                        for exp in dados:
                            nome = exp.get("title", "Desconhecido")
                            versao = exp.get("version", "")
                            atualizado = exp.get("updateStatus", False)
                            
                            status_emoji = "<:zw_GreenCircle:1547801001241608315>" if atualizado else "<:zw_RedCircle:1547800979242745876>"
                            linha = f"- {nome} | `{versao}` | {status_emoji}"
                            
                            nome_lower = nome.lower()
                            plataforma = str(exp.get("platform", "")).lower()
                            tipo = str(exp.get("type", "")).lower()
                            is_external = exp.get("isExternal", False) or exp.get("external", False)
                            
                            if "mac" in plataforma or "mac" in tipo or "mac" in nome_lower:
                                mac_exploits.append(linha)
                            elif is_external or any(ext in nome_lower for ext in nomes_externals_conhecidos) or "external" in tipo:
                                windows_externals.append(linha)
                            else:
                                windows_exploits.append(linha)
                    
                    textos_corpo = []
                    if windows_exploits:
                        textos_corpo.append("**Windows Exploits**\n" + "\n".join(windows_exploits))
                    if mac_exploits:
                        textos_corpo.append("\n**Mac Exploits**\n" + "\n".join(mac_exploits))
                    if windows_externals:
                        textos_corpo.append("\n**Windows Externals**\n" + "\n".join(windows_externals))
                        
                    ultimo_corpo_texto = "\n".join(textos_corpo).strip()
                    payload = construir_payload(ultimo_corpo_texto)

                    async with aiohttp.ClientSession() as session_disc:
                        headers_discord = {
                            "Authorization": f"Bot {os.environ.get('DISCORD_TOKEN')}",
                            "Content-Type": "application/json"
                        }
                        
                        if id_ultima_mensagem:
                            edit_url = f"https://discord.com/api/v10/channels/{CANAL_ID}/messages/{id_ultima_mensagem}"
                            async with session_disc.patch(edit_url, json=payload, headers=headers_discord) as resp:
                                if resp.status == 200:
                                    return

                        send_url = f"https://discord.com/api/v10/channels/{CANAL_ID}/messages"
                        async with session_disc.post(send_url, json=payload, headers=headers_discord) as resp:
                            if resp.status == 200:
                                data_resp = await resp.json()
                                id_ultima_mensagem = data_resp.get("id")
    except Exception as e:
        print(f"Erro no loop da API: {e}")

@tasks.loop(minutes=1)
async def atualizar_tempo_ui():
    global id_ultima_mensagem, ultimo_corpo_texto
    if not id_ultima_mensagem or not ultimo_corpo_texto:
        return
        
    try:
        payload = construir_payload(ultimo_corpo_texto)
        async with aiohttp.ClientSession() as session:
            headers_discord = {
                "Authorization": f"Bot {os.environ.get('DISCORD_TOKEN')}",
                "Content-Type": "application/json"
            }
            edit_url = f"https://discord.com/api/v10/channels/{CANAL_ID}/messages/{id_ultima_mensagem}"
            async with session.patch(edit_url, json=payload, headers=headers_discord) as resp:
                pass
    except Exception as e:
        print(f"Erro ao atualizar o tempo na UI: {e}")

@sincronizar_api.before_loop
@atualizar_tempo_ui.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

async def handle(request):
    return web.Response(text="Bot do Discord a funcionar 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Servidor web a correr na porta {port}")

async def main():
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("ERRO: Variável DISCORD_TOKEN em falta!")
        return

    await start_web_server()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
