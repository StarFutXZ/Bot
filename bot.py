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

    url = "[https://weao.xyz/api/status/exploits](https://weao.xyz/api/status/exploits)"
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
                            
                            status_emoji = "✅" if atualizado else "❌"
                            linha = f"• {nome:<12} | {versao:<8} {status_emoji}"
                            
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
                    
                    # Constrói o painel dentro de um bloco de código fechado (caixa)
                    bloco_texto = "========================================\n"
                    bloco_texto += "        WHATEXPSARE.ONLINE STATUS       \n"
                    bloco_texto += "========================================\n\n"
                    
                    if windows_exploits:
                        bloco_texto += "[ WINDOWS EXPLOITS ]\n"
                        bloco_texto += "\n".join(windows_exploits) + "\n\n"
                        
                    if mac_exploits:
                        bloco_texto += "[ MAC EXPLOITS ]\n"
                        bloco_texto += "\n".join(mac_exploits) + "\n\n"
                        
                    if windows_externals:
                        bloco_texto += "[ WINDOWS EXTERNALS ]\n"
                        bloco_texto += "\n".join(windows_externals) + "\n\n"
                        
                    bloco_texto += "----------------------------------------\n"
                    bloco_texto += "Powered by weao.xyz"
                    
                    descricao_final = f"```\n{bloco_texto}\n```"
                    
                    if id_ultima_mensagem and descricao_final == ultimo_conteudo_enviado:
                        print("Sem alterações nos status. Nenhuma edição necessária.")
                        return
                    
                    ultimo_conteudo_enviado = descricao_final
                    
                    embed = discord.Embed(
                        description=descricao_final,
                        color=discord.Color.from_str("#ff0000")
                    )
                    
                else:
                    embed = discord.Embed(
                        title="Erro",
                        description="```\n⚠️ Erro ao aceder à API de status da WEAO.\n```",
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
