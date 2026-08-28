import discord
from discord.ext import tasks, commands
import aiohttp
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

id_ultima_mensagem = None
ultimo_conteudo_enviado = None  # Guarda o texto da última descrição para comparar
CANAL_ID = 1542669778999574599  # Substitui pelo ID real do teu canal

@bot.event
async def on_ready():
    print(f"Bot ligado com sucesso como {bot.user}")
    if not enviar_ou_atualizar.is_running():
        enviar_ou_atualizar.start()

@tasks.loop(minutes=15)
async def enviar_ou_atualizar():
    global id_ultima_mensagem, ultimo_conteudo_enviado
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
    except (discord.NotFound, discord.Forbidden):
        print("Erro ao aceder ao canal.")
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
                    
                    if isinstance(dados, list):
                        for exp in dados:
                            nome = exp.get("title", "Desconhecido")
                            versao = exp.get("version", "")
                            atualizado = exp.get("updateStatus", False)
                            
                            status_emoji = "🟩" if atualizado else "🟥"
                            linha = f"{nome} | `{versao}` | {status_emoji}"
                            
                            tipo = str(exp.get("type", "")).lower()
                            plataforma = str(exp.get("platform", "")).lower()
                            
                            if "mac" in plataforma or "mac" in tipo:
                                mac_exploits.append(linha)
                            elif "external" in tipo or "external" in plataforma:
                                windows_externals.append(linha)
                            else:
                                windows_exploits.append(linha)
                    
                    descricao_final = ""
                    if windows_exploits:
                        descricao_final += "**Windows Exploits**\n" + "\n".join(windows_exploits) + "\n\n"
                    if mac_exploits:
                        descricao_final += "**Mac Exploits**\n" + "\n".join(mac_exploits) + "\n\n"
                    if windows_externals:
                        descricao_final += "**Windows Externals**\n" + "\n".join(windows_externals) + "\n\n"
                        
                    descricao_final = descricao_final.strip()
                    
                    # Se o conteúdo for exatamente igual ao anterior e a mensagem já existir, não faz nada!
                    if id_ultima_mensagem and descricao_final == ultimo_conteudo_enviado:
                        print("Sem alterações nos exploits. Nenhuma edição necessária.")
                        return
                    
                    # Atualiza o registo do último conteúdo
                    ultimo_conteudo_enviado = descricao_final
                    
                    embed = discord.Embed(
                        title="WhatExpsAre.Online | Exploit Status",
                        description=descricao_final,
                        color=discord.Color.from_rgb(40, 40, 45)
                    )
                    embed.set_footer(text="Powered by weao.xyz")
                    
                else:
                    embed = discord.Embed(
                        title="Erro",
                        description="⚠️ Erro ao aceder à API de status da WEAO.",
                        color=discord.Color.red()
                    )
    except Exception as e:
        embed = discord.Embed(
            title="Erro de Ligação",
            description=f"⚠️ Erro: {e}",
            color=discord.Color.red()
        )

    # Envia ou edita a mensagem apenas se houve mudanças ou se for a primeira vez
    mensagem_editada = False
    if id_ultima_mensagem:
        try:
            msg = await canal.fetch_message(id_ultima_mensagem)
            await msg.edit(embed=embed)
            mensagem_editada = True
        except (discord.NotFound, discord.HTTPException):
            mensagem_editada = False

    if not mensagem_editada:
        nova_msg = await canal.send(embed=embed)
        id_ultima_mensagem = nova_msg.id

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

bot.run(os.environ.get('DISCORD_TOKEN'))
