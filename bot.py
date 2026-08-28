import discord
from discord.ext import tasks, commands
import aiohttp
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

ids_ultimas_mensagens = []
ultimo_conteudo_enviado = None

CANAL_ID = 1542669778999574599

CHECK_EMOJI = "<:zw_check:1542714478322393139>"
X_EMOJI = "<:zw_x:1542714561717731368>"


@bot.event
async def on_ready():
    global ids_ultimas_mensagens

    print(f"Bot ligado com sucesso como {bot.user}")

    try:
        canal = await bot.fetch_channel(CANAL_ID)

        ids_ultimas_mensagens = []

        async for mensagem in canal.history(limit=20):
            if mensagem.author.id == bot.user.id and mensagem.embeds:
                ids_ultimas_mensagens.append(mensagem.id)

                if len(ids_ultimas_mensagens) >= 3:
                    break

        if ids_ultimas_mensagens:
            print(
                f"Mensagens anteriores detetadas "
                f"(IDs: {ids_ultimas_mensagens})."
            )

    except Exception as e:
        print(f"Erro ao procurar mensagens anteriores: {e}")

    if not enviar_ou_atualizar.is_running():
        enviar_ou_atualizar.start()
        print("Loop de 15 minutos iniciado com sucesso!")


@tasks.loop(minutes=15)
async def enviar_ou_atualizar():

    global ids_ultimas_mensagens
    global ultimo_conteudo_enviado

    print("A verificar atualizações da API WEAO...")

    try:
        canal = await bot.fetch_channel(CANAL_ID)

    except (discord.NotFound, discord.Forbidden):
        print("Erro ao aceder ao canal do Discord.")
        return

    url = "https://weao.xyz/api/status/exploits"

    headers = {
        "User-Agent": "WEAO-3PService"
    }

    try:

        async with aiohttp.ClientSession(headers=headers) as session:

            async with session.get(url) as response:

                if response.status != 200:
                    print(
                        f"API respondeu com status {response.status}"
                    )
                    return

                dados = await response.json()

        windows_exploits = []
        mac_exploits = []
        windows_externals = []

        nomes_externals_conhecidos = [
            "serotonin",
            "matcha",
            "severe",
            "lumen",
            "matrix hub",
            "melatonin",
            "axis",
            "photon",
            "ronin",
            "dx9ware v2",
            "dx9ware"
        ]

        # -----------------------------------------
        # ORGANIZAR OS DADOS DA API
        # -----------------------------------------

        if isinstance(dados, list):

            for exp in dados:

                nome = exp.get(
                    "title",
                    "Desconhecido"
                )

                versao = exp.get(
                    "version",
                    ""
                )

                atualizado = exp.get(
                    "updateStatus",
                    False
                )

                if atualizado:
                    status_emoji = CHECK_EMOJI
                else:
                    status_emoji = X_EMOJI

                linha = (
                    f"{nome} | `{versao}` | {status_emoji}"
                )

                nome_lower = nome.lower()

                plataforma = str(
                    exp.get("platform", "")
                ).lower()

                tipo = str(
                    exp.get("type", "")
                ).lower()

                is_external = (
                    exp.get("isExternal", False)
                    or exp.get("external", False)
                )

                # MAC
                if (
                    "mac" in plataforma
                    or "mac" in tipo
                    or "mac" in nome_lower
                ):
                    mac_exploits.append(linha)

                # EXTERNAL
                elif (
                    is_external
                    or any(
                        ext in nome_lower
                        for ext in nomes_externals_conhecidos
                    )
                    or "external" in tipo
                ):
                    windows_externals.append(linha)

                # WINDOWS
                else:
                    windows_exploits.append(linha)

        # -----------------------------------------
        # CONTEÚDO PARA DETETAR ALTERAÇÕES
        # -----------------------------------------

        seccoes = []

        if windows_exploits:
            seccoes.append(
                "**Windows Exploits**\n"
                + "\n".join(windows_exploits)
            )

        if mac_exploits:
            seccoes.append(
                "**Mac Exploits**\n"
                + "\n".join(mac_exploits)
            )

        if windows_externals:
            seccoes.append(
                "**Windows Externals**\n"
                + "\n".join(windows_externals)
            )

        conteudo_total = "\n\n".join(seccoes)

        # -----------------------------------------
        # NÃO ATUALIZ
