import discord
from discord.ext import tasks, commands
import aiohttp
import aiohttp.web as web
import os
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

id_ultima_mensagem = None
ultimo_conteudo_enviado = None
CANAL_ID = 1542669778999574599  # Substitui pelo ID real do teu canal

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Servidor web a correr na porta {port}")

@bot.event
async def on_ready():
    global id_ultima_mensagem
    print(f"Bot ligado com sucesso como {bot.user}")
    
    try:
        canal = await bot.fetch_channel(CANAL_ID)
        async for mensagem in canal.history(limit=20):
            if mensagem.author.id == bot.user.id and mensagem.embeds:
                id_ultima_mensagem = mensagem.id
                print(f"Mensagem anterior detetada (ID: {id_ultima_mensagem}).")
                break
    except Exception as e:
        print(f"Erro ao procurar mensagem anterior: {e}")

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
                            
                            # Emojis personalizados integrados para verde e vermelho
                            status_emoji = "<:zw_check:1542714478322393139>" if atualizado else "<:zw_x:1542714561717731368>"
                            
                            linha = f"{nome} | `{versao}` | {status_emoji}"
                            
                            tipo = str(exp.get("type", "")).lower()
                            plataforma = str(exp.get("platform", "")).lower()
                            is_external = exp.get("isExternal", False) or exp.get("external", False) or "external" in tipo or "externals" in tipo
                            
                            if "mac" in plataforma or "mac" in tipo:
                                mac_exploits.append(linha)
                            elif is_external:
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
                    
                    if id_ultima_mensagem and descricao_final == ultimo_conteudo_enviado:
                        print("Sem alterações nos exploits. Nenhuma edição necessária.")
                        return
                    
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

    mensagem_editada = False
    if id_ultima_mensagem:
        try:
            msg = await canal.fetch_message(id_ultima_mensagem)
            await msg.edit(embed=embed)
            mensagem_editada = True
        except (discord.NotFound, discord.HTTPException):
            mensagem_editada = False

    if not mensagem_editada:
        try:
            async for mensagem in canal.history(limit=10):
                if mensagem.author.id == bot.user.id:
                    await mensagem.delete()
        except Exception:
            pass
            
        nova_msg = await canal.send(embed=embed)
        id_ultima_mensagem = nova_msg.id

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

async def main():
    await start_web_server()
    await bot.start(os.environ.get('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())
