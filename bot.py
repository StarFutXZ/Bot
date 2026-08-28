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
                            
                            # Visual alterado para ficar exatamente igual ao da imagem (Nome | `Versão` | Emoji)
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
                    
                    # Constrói blocos de texto por secção
                    seccoes = []
                    if windows_exploits:
                        seccoes.append("**Windows Exploits**\n" + "\n".join(windows_exploits))
                    if mac_exploits:
                        seccoes.append("**Mac Exploits**\n" + "\n".join(mac_exploits))
                    if windows_externals:
                        seccoes.append("**Windows Externals**\n" + "\n".join(windows_externals))
                        
                    conteudo_total = "\n\n".join(seccoes)
                    
                    if ids_ultimas_mensagens and conteudo_total == ultimo_conteudo_enviado:
                        print("Sem alterações nos status. Nenhuma edição necessária.")
                        return
                    
                    ultimo_conteudo_enviado = conteudo_total
                    
                    # Lógica inteligente para dividir em múltiplos embeds caso passe dos 3900 carateres (margem de segurança)
                    embeds_para_enviar = []
                    bloco_atual = ""
                    
                    for seccao in seccoes:
                        if len(bloco_atual) + len(seccao) + 2 > 3900:
                            # Cria o embed com o bloco atual e começa um novo
                            emb = discord.Embed(
                                title="WhatExpsAre.Online | Exploit Status (Continuação)",
                                description=bloco_atual.strip(),
                                color=discord.Color.from_rgb(40, 40, 45)
                            )
                            embeds_para_enviar.append(emb)
                            bloco_atual = seccao + "\n\n"
                        else:
                            bloco_atual += seccao + "\n\n"
                            
                    # Adiciona o último bloco restante
                    if bloco_atual:
                        titulo = "WhatExpsAre.Online | Exploit Status" if len(embeds_para_enviar) == 0 else "WhatExpsAre.Online | Exploit Status (Continuação)"
                        emb = discord.Embed(
                            title=titulo,
                            description=bloco_atual.strip(),
                            color=discord.Color.from_rgb(40, 40, 45)
                        )
                        # Coloca o rodapé apenas no último embed
                        emb.set_footer(text="Powered by weao.xyz")
                        embeds_para_enviar.append(emb)
                        
                else:
                    embeds_para_enviar = [discord.Embed(
                        title="Erro",
                        description="⚠️ Erro ao aceder à API de status da WEAO.",
                        color=discord.Color.red()
                    )]
    except Exception as e:
        print(f"Erro no pedido HTTP: {e}")
        return

    # Apaga as mensagens antigas do bot para evitar acumulação de lixo no canal
    if ids_ultimas_mensagens:
        for msg_id in ids_ultimas_mensagens:
            try:
                msg_antiga = await canal.fetch_message(msg_id)
                await msg_antiga.delete()
            except Exception:
                pass
        ids_ultimas_mensagens = []

    # Envia os novos embeds (pode ser 1 ou mais se exceder o limite)
    try:
        # O discord permite enviar até 10 embeds numa única mensagem
        nova_msg = await canal.send(embeds=embeds_para_enviar)
        ids_ultimas_mensagens = [nova_msg.id]
        print("Status atualizados com sucesso (múltiplos embeds tratados em mensagem única).")
    except Exception as e:
        print(f"Erro ao enviar a mensagem com os embeds: {e}")

@enviar_ou_atualizar.before_loop
async def antes_de_comecar():
    await bot.wait_until_ready()

token = os.environ.get('DISCORD_TOKEN')
if not token:
    print("ERRO: Variável DISCORD_TOKEN em falta!")
else:
    bot.run(token)
