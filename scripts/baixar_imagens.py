"""
Baixa as imagens das ofertas. Roda no GitHub Actions (que tem internet
liberada), porque o ambiente do Claude não acessa os servidores de imagem
do Mercado Livre.

Entrada:  dados/imagens_pendentes.csv  (colunas: nome, url)
Saída:    pasta imagens_baixadas/ com um JPG por linha (nome.jpg)

As imagens são convertidas para JPG de até 800px, fundo branco,
que é o formato que o WhatsApp aceita sem problema.
"""

import csv
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ENTRADA = PASTA_PROJETO / "dados" / "imagens_pendentes.csv"
SAIDA = PASTA_PROJETO / "imagens_baixadas"


def baixar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return resposta.read()


def para_jpg(dados, destino, lado_max=800):
    img = Image.open(io.BytesIO(dados)).convert("RGBA")
    img.thumbnail((lado_max, lado_max))
    fundo = Image.new("RGB", img.size, (255, 255, 255))  # fundo branco
    fundo.paste(img, mask=img.split()[3])
    fundo.save(destino, "JPEG", quality=85)


def main():
    SAIDA.mkdir(exist_ok=True)
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))

    falhas = 0
    for linha in linhas:
        destino = SAIDA / f"{linha['nome']}.jpg"
        try:
            para_jpg(baixar(linha["url"]), destino)
            print(f"ok    {destino.name}")
        except Exception as erro:
            falhas += 1
            print(f"FALHA {linha['nome']}: {erro}")

    print(f"\n{len(linhas) - falhas} de {len(linhas)} imagens baixadas.")
    if falhas == len(linhas) and linhas:
        sys.exit(1)  # nenhuma imagem baixou: marca a execução como erro


if __name__ == "__main__":
    main()
