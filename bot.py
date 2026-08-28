import discord
from discord.ext import tasks, commands
import aiohttp
import os
import asyncio

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
            if mensagem.author.id == bot.user.id and mensagem.embeds:
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
                            linha = f"• **{nome}** — `{versao}` {status_emoji}"
                            
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
                    
                    # Constrói o Embed principal com o aspeto de painel em caixa, sem botões
                    embed = discord.Embed(
                        title="⚡ Exploit Status Tracker",
                        description="A atualização dos executores foi detetada!",
                        color=discord.Color.from_str("#2b2d31")
                    )
                    
                    if windows_exploits:
                        embed.add_field(name="🖥️ Windows Exploits", value="\n".join(windows_exploits), inline=False)
                    if mac_exploits:
                        embed.add_field(name="💻 Mac Exploits", value="\n".join(mac_exploits), inline=False)
                    if windows_externals:
                        embed.add_field(name="🔌 Windows Externals", value="\n".join(windows_externals), inline=False)
                        
                    embed.set_footer(text="Powered by weao.xyz")
                    
                    conteudo_comparacao = "".join(windows_exploits + mac_exploits + windows_externals)
                    if id_ultima_mensagem and conteudo_comparacao == ultimo_conteudo_enviado:
                        print("Sem alterações nos status. Nenhuma edição necessária.")
                        return
                    
                    ultimo_conteudo_enviado = conteudo_comparacao
                    
                else:
                    embed = discord.Embed(
                        title="Erro",
                        description="⚠️ Erro ao aceder à API de status da WEAO.",
                        color=discord.Color.red()
                    )
    except Exception as e:
        print(f"Erro no pedido HTTP: {e}")
        return

    mensagem_editada = False
    if id_ultima_mensagem:
        try:
            msg = await canal.fetch_message(id_ultima_mensagem)
            await msg.edit(embed=embed)
            print("Mensagem editada com sucesso.")
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
        print("Nova mensagem enviada.")

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

token = os.environ.get('DISCORD_TOKEN')
if not token:
    print("ERRO: Variável DISCORD_TOKEN em falta!")
else:
    bot.run(token)
