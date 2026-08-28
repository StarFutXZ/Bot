import discord
from discord.ext import tasks, commands
import aiohttp

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ultima_mensagem = None
CANAL_ID = 1542669778999574599  

@bot.event
async def on_ready():
    print(f"Bot ligado com sucesso como {bot.user}")
    enviar_ou_atualizar.start()

@tasks.loop(minutes=15)
async def enviar_ou_atualizar():
    global ultima_mensagem
    
    canal = bot.get_channel(CANAL_ID)
    if not canal:
        print("Canal não encontrado!")
        return

    # Vai buscar os dados atualizados à API da WEAO
    url = "https://weao.xyz/api/status/exploits"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    exploits = await response.json()
                    
                    # Constrói o texto com o estado dos principais exploits
                    texto_status = "🟢 **WhatExpsAre.Online | Exploit Status**\n\n"
                    
                    for exp in exploits[:10]: # Limita aos primeiros para caber na mensagem
                        nome = exp.get("title", "Desconhecido")
                        versao = exp.get("version", "")
                        atualizado = exp.get("updated", False)
                        status_emoji = "✅" if atualizado else "❌"
                        texto_status += f"- **{nome}** | `{versao}` | {status_emoji}\n"
                        
                else:
                    texto_status = "⚠️ Erro ao aceder à API de status da WEAO."
    except Exception as e:
        texto_status = f"⚠️ Erro na ligação: {e}"

    # Apaga a mensagem anterior se existir
    if ultima_mensagem:
        try:
            await ultima_mensagem.delete()
        except discord.HTTPException:
            pass

    # Envia a nova mensagem atualizada
    ultima_mensagem = await canal.send(texto_status)

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

bot.run('MTIxNjQyMDc0NTY0MzU1NjkzNA.GX1qyG.3dsc58Z7ztxY06SOQPaNgtpoZFjG0yyjiT54H0')
