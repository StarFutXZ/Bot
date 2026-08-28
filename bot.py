import discord
from discord.ext import tasks, commands
import aiohttp
import os
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Agora guardamos listas de IDs de mensagens para suportar múltiplos embeds se necessário
ids_ultimas_mensagens = []
ultimo_conteudo_enviado = None
CANAL_ID = 1542669778999574599  # ID do teu canal

@bot.event
async def on_ready():
    global ids_ultimas_mensagens
    print(f"Bot ligado com sucesso como {bot.user}")
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
        # Procura mensagens anteriores do bot no canal
        ids_ultimas_mensagens = []
        async for mensagem in canal.history(limit=20):
            if mensagem.author.id == bot.user.id and mensagem.embeds:
                ids_ultimas_mensagens.append(mensagem.id)
                # Se encontrarmos mensagens consecutivas do bot, apanhamos todas para atualizar depois
                if len(ids_ultimas_mensagens) >= 3:
                    break
        if ids_ultimas_mensagens:
            print(f"Mensagens anteriores detetadas (IDs: {ids_ultimas_mensagens}).")
    except Exception as e:
        print(f"Erro ao procurar mensagens anteriores: {e}")

    if not enviar_ou_atualizar.is_running():
        enviar_ou_atualizar.start()
        print("Loop de 15 minutos iniciado com sucesso!")

@tasks.loop(minutes=15)
async def enviar_ou_atualizar():
    global ids_ultimas_mensagens, ultimo_conteudo_enviado
    
    print("A verificar atualizações da API WEAO...")
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
    except (discord.NotFound, discord.Forbidden):
        print("Erro ao aceder ao canal do Discord.")
        return

    url = "https://weao.xyz/api/status/exploits"
    headers = {"User-Agent": "WEAO-3PService"}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
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
                            linha = f"{nome} | `{versao}` | {status_emoji}"
                            
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
                    
                    # Constrói blocos de texto por secção com as caixas de código (estilo painel técnico)
                    seccoes = []
                    if windows_exploits:
                        bloco_win = "**Windows Exploits**\n```\n" + "\n".join(windows_exploits) + "\n```"
                        seccoes.append(bloco_win)
                    if mac_exploits:
                        bloco_mac = "**Mac Exploits**\n```\n" + "\n".join(mac_exploits) + "\n```"
                        seccoes.append(bloco_mac)
                    if windows_externals:
                        bloco_ext = "**Windows Externals**\n```\n" + "\n".join(windows_externals) + "\n
