import discord
from discord.ext import tasks, commands
import aiohttp
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ID da mensagem anterior guardado em memória
id_ultima_mensagem = None
CANAL_ID = 1542669778999574599  # Lembra-te de meter o ID real do teu canal!

@bot.event
async def on_ready():
    print(f"Bot ligado com sucesso como {bot.user}")
    if not enviar_ou_atualizar.is_running():
        enviar_ou_atualizar.start()

@tasks.loop(minutes=15)
async def enviar_ou_atualizar():
    global id_ultima_mensagem
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
    except discord.NotFound:
        print("Canal não encontrado! Verifica se o ID está correto.")
        return
    except discord.Forbidden:
        print("O bot não tem permissões para aceder a este canal!")
        return

    # Procura a resposta na API da WEAO
    url = "https://weao.xyz/api/status/exploits"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    exploits = await response.json()
                    
                    texto_status = "🟢 **WhatExpsAre.Online | Exploit Status**\n\n"
                    
                    for exp in exploits[:10]:
                        nome = exp.get("title", "Desconhecido")
                        versao = exp.get("version", "")
                        atualizado = exp.get("updated", False)
                        status_emoji = "✅" if atualizado else "❌"
                        texto_status += f"- **{nome}** | `{versao}` | {status_emoji}\n"
                else:
                    texto_status = "⚠️ Erro ao aceder à API de status da WEAO."
    except Exception as e:
        texto_status = f"⚠️ Erro na ligação: {e}"

    # Tenta editar a mensagem anterior para não encher o chat
    mensagem_editada = False
    if id_ultima_mensagem:
        try:
            msg = await canal.fetch_message(id_ultima_mensagem)
            await msg.edit(content=texto_status)
            mensagem_editada = True
        except (discord.NotFound, discord.HTTPException):
            mensagem_editada = False

    # Se não conseguiu editar (ex: primeira execução ou mensagem foi apagada), envia uma nova
    if not mensagem_editada:
        nova_msg = await canal.send(texto_status)
        id_ultima_mensagem = nova_msg.id

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

bot.run(os.environ.get('DISCORD_TOKEN'))
