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
ultimo_conteudo_enviado = None
CANAL_ID = 1542669778999574599  # ID do teu canal

@bot.event
async def on_ready():
    global id_ultima_mensagem
    print(f"Bot ligado com sucesso como {bot.user}")
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
        async for mensagem in canal.history(limit=20):
            if mensagem.author.id == bot.user.id:
                id_ultima_mensagem = mensagem.id
                print(f"Mensagem anterior detetada (ID: {id_ultima_mensagem}).")
                break
    except Exception as e:
        print(f"Erro ao procurar mensagem anterior: {e}")

    if not enviar_ou_atualizar.is_running():
        enviar_ou_atualizar.start()
        print("Loop de 15 minutos iniciado com sucesso!")

@tasks.loop(minutes=15)
async def enviar_ou_atualizar():
    global id_ultima_mensagem, ultimo_conteudo_enviado
    
    try:
        print("A verificar atualizações da API WEAO...")
        
        try:
            canal = await bot.fetch_channel(CANAL_ID)
        except (discord.NotFound, discord.Forbidden):
            print("Erro ao aceder ao canal do Discord.")
            return

        url = "https://weao.xyz/api/status/exploits"
        headers = {"User-Agent": "WEAO-3PService"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    dados = await response.json()
                    
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
                            
                            status_emoji = "<:zw_check:1542714478322393139>" if atualizado else "<:zw_x:1542714561717731368>"
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
                    
                    textos_container = []
                    textos_container.append("### WhatExpsAre.Online | Exploit Status\n")
                    
                    if windows_exploits:
                        textos_container.append("**Windows Exploits**\n" + "\n".join(windows_exploits))
                    if mac_exploits:
                        textos_container.append("\n**Mac Exploits**\n" + "\n".join(mac_exploits))
                    if windows_externals:
                        textos_container.append("\n**Windows Externals**\n" + "\n".join(windows_externals))
                        
                    corpo_texto = "\n".join(textos_container).strip()
                    
                    hora_portugal = datetime.now(ZoneInfo("Europe/Lisbon")).strftime('%H:%M')
                    footer_texto = f"⏳ Stock Change in • Atualizado às {hora_portugal}"
                    
                    conteudo_total = f"{corpo_texto}\n\n-# {footer_texto}"
                    ultimo_conteudo_enviado = conteudo_total

                    # Payload utilizando componentes V2 para eliminar o embed tradicional e aplicar o container com barra lateral
                    payload = {
                        "flags": 32768,  # Ativa o modo de componentes V2
                        "components": [
                            {
                                "type": 17,  # Componente do tipo Container
                                "accent_color": 2829609,  # Cor da barra lateral do container
                                "components": [
                                    {
                                        "type": 10,  # Componente do tipo TextDisplay para o conteúdo interno
                                        "content": conteudo_total
                                    }
                                ]
                            }
                        ]
                    }
                    
                else:
                    payload = {
                        "flags": 32768,
                        "components": [
                            {
                                "type": 17,
                                "accent_color": 15158332,
                                "components": [
                                    {
                                        "type": 10,
                                        "content": "⚠️ **Erro**\n-# Erro ao aceder à API de status da WEAO."
                                    }
                                ]
                            }
                        ]
                    }

        # Envio e edição via API REST v10 do Discord
        async with aiohttp.ClientSession() as session:
            headers_discord = {
                "Authorization": f"Bot {os.environ.get('DISCORD_TOKEN')}",
                "Content-Type": "application/json"
            }
            
            if id_ultima_mensagem:
                edit_url = f"https://discord.com/api/v10/channels/{CANAL_ID}/messages/{id_ultima_mensagem}"
                async with session.patch(edit_url, json=payload, headers=headers_discord) as resp:
                    if resp.status == 200:
                        print("Mensagem em Container V2 editada com sucesso.")
                        return

            send_url = f"https://discord.com/api/v10/channels/{CANAL_ID}/messages"
            async with session.post(send_url, json=payload, headers=headers_discord) as resp:
                if resp.status == 200:
                    data_resp = await resp.json()
                    id_ultima_mensagem = data_resp.get("id")
                    print("Nova mensagem em Container V2 enviada com sucesso.")
                else:
                    print(f"Erro ao enviar Container V2: {await resp.text()}")
            
    except Exception as e:
        print(f"Erro crítico apanhado no loop principal: {e}")

@enviar_ou_atualizar.before_loop
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
