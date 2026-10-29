"""
Junta tudo da rodada num único arquivo para o gerar_posts.py.

Entradas:
  dados/rodada/selecionadas.json -> ofertas escolhidas (selecionar_ofertas.py)
  dados/rodada/links.json        -> resultado do link_afiliado.js para cada oferta:
      { "<id_anuncio>": {"preco": 30.94, "anvisa": 1, "link": "https://meli.la/..."}, ... }
  <pasta_imagens>                -> pasta com <id_anuncio>.jpg (branch "imagens")

Regras:
  - sem link de afiliado: fica de fora
  - produto profissional (insumo, descartável, odonto...) sem "Anvisa" no anúncio: fica de fora
  - preço mudou na página: usa o preço novo; se o desconto cair abaixo do mínimo, fica de fora

Saídas:
  dados/ofertas_rodada.csv  -> entrada do gerar_posts.py
  dados/termos_usados.csv   -> registro do rodízio (data, termo, achou)

Como rodar:
  python scripts/montar_rodada.py <pasta_imagens>
"""

import csv
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import nicho  # pastas e preferências do nicho (NICHO=aquarismo, etc.)

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RODADA = nicho.PASTA_RODADA
ARQ_SAIDA = nicho.PASTA_DADOS / "ofertas_rodada.csv"
ARQ_USADOS = nicho.PASTA_DADOS / "termos_usados.csv"

# Categorias de dispositivos médicos: precisam de pelo menos UM sinal de confiança
# (anúncio cita a Anvisa, OU marca da lista config/marcas_confiaveis.csv, OU loja oficial)
EXIGE_CONFIANCA = nicho.EXIGE_CONFIANCA  # definido em config/<nicho>/nicho.json
ARQ_MARCAS = nicho.PASTA_CONFIG / "marcas_confiaveis.csv"


def sem_acento(t):
    return unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()


def ler_marcas():
    if not ARQ_MARCAS.exists():
        return []
    with open(ARQ_MARCAS, encoding="utf-8", newline="") as f:
        return [sem_acento(l["marca"].strip()) for l in csv.DictReader(f) if l["marca"].strip()]


def marca_confiavel(titulo, marcas):
    """Devolve a marca confiável que aparece no título (palavra inteira), ou None."""
    t = sem_acento(titulo)
    return next((m for m in marcas if re.search(r"(^|[^a-z0-9])" + re.escape(m) + r"([^a-z0-9]|$)", t)), None)


def sinal_de_confianca(o, info, marcas):
    """Explica por que o produto é confiável, ou devolve None."""
    if nicho.MOSTRAR_ANVISA and info.get("anvisa"):
        return "anvisa"
    marca = marca_confiavel(o["titulo"] + " " + info.get("titulo", ""), marcas)
    if marca:
        return f"marca {marca}"
    if info.get("loja_oficial"):
        return "loja oficial"
    return None


def mesmo_produto(titulo_escolhido, titulo_pagina):
    """
    Trava de segurança: confere se a página aberta é do produto escolhido.
    Pelo menos metade das palavras importantes (4+ letras) do título escolhido
    precisa aparecer no título da página.
    """
    if not titulo_pagina:
        return False
    def palavras(t):
        t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
        return {p for p in re.findall(r"[a-z0-9]+", t) if len(p) >= 4}
    escolhidas = palavras(titulo_escolhido)
    if not escolhidas:
        return True
    return len(escolhidas & palavras(titulo_pagina)) / len(escolhidas) >= 0.5


def titulo_curto(titulo, limite=70):
    """Corta títulos longos na última palavra inteira."""
    if len(titulo) <= limite:
        return titulo
    return titulo[:limite].rsplit(" ", 1)[0]


def por_que_vale(o, anvisa):
    """Monta a linha de 'por que vale' com fatos do anúncio."""
    partes = []
    v = o["vendidos"] or 0
    if v >= 1000:
        partes.append(f"Mais de {int(v // 1000)} mil vendidos")
    elif v >= 100:
        partes.append(f"Mais de {int(v)} vendidos")
    if o["full"]:
        partes.append("envio Full")
    elif o["frete_gratis"]:
        partes.append("frete grátis")
    if anvisa and nicho.MOSTRAR_ANVISA:
        partes.append("registro Anvisa")
    texto = " · ".join(partes)
    return texto[:1].upper() + texto[1:] if texto else ""


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/montar_rodada.py <pasta_imagens>")
        return
    pasta_imagens = Path(sys.argv[1])
    selecionadas = json.loads((PASTA_RODADA / "selecionadas.json").read_text(encoding="utf-8"))
    links_arq = PASTA_RODADA / "links.json"
    links = json.loads(links_arq.read_text(encoding="utf-8")) if links_arq.exists() else {}

    marcas = ler_marcas()
    linhas, usados = [], []
    for o in selecionadas:
        info = links.get(o["id_anuncio"], {})
        achou = False
        if info and not mesmo_produto(o["titulo"], info.get("titulo", "")):
            print(f"✖ a página aberta era de OUTRO produto ({info.get('titulo', '?')[:40]}): {o['titulo'][:45]}")
        elif not info.get("link"):
            print(f"✖ sem link de afiliado: {o['titulo'][:55]} ({info.get('erro', 'não gerado')})")
        elif o["categoria"] in EXIGE_CONFIANCA and not sinal_de_confianca(o, info, marcas):
            print(f"✖ sem Anvisa, marca confiável ou loja oficial: {o['titulo'][:55]}")
        else:
            por = info.get("preco") or o["preco_por"]
            de = max(o["preco_de"], por)
            desconto = round((1 - por / de) * 100) if de > por else 0
            if por != o["preco_por"]:
                print(f"  preço mudou: {o['titulo'][:45]}  {o['preco_por']} -> {por}")
            if desconto < o["desconto_min"]:
                print(f"✖ desconto caiu para {desconto}%: {o['titulo'][:55]}")
            else:
                imagem = pasta_imagens / f"{o['id_anuncio']}.jpg"
                if not imagem.exists():
                    print(f"  ⚠️ sem imagem baixada: {o['titulo'][:55]}")
                linhas.append({
                    "id_anuncio": o["id_anuncio"],
                    "titulo": titulo_curto(o["titulo"]),
                    "categoria": o["categoria"],
                    "preco_de": f"{de:.2f}".replace(".", ","),
                    "preco_por": f"{por:.2f}".replace(".", ","),
                    "so_pix": "sim" if o["so_pix"] else "nao",
                    "por_que_vale": por_que_vale(o, info.get("anvisa")),
                    "link_afiliado": info["link"],
                    "url_imagem": "",
                    "arquivo_imagem": str(imagem) if imagem.exists() else "",
                })
                achou = True
        usados.append({"data": date.today().isoformat(), "termo": o["termo"], "achou": "sim" if achou else "nao"})

    # Termos buscados que não renderam oferta também entram no rodízio,
    # para não serem sorteados de novo logo em seguida
    termos = json.loads((PASTA_RODADA / "termos.json").read_text(encoding="utf-8"))
    ja = {u["termo"] for u in usados}
    usados += [{"data": date.today().isoformat(), "termo": t["termo"], "achou": "nao"}
               for t in termos if t["termo"] not in ja]

    with open(ARQ_SAIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id_anuncio", "titulo", "categoria", "preco_de", "preco_por",
                                          "so_pix", "por_que_vale", "link_afiliado", "url_imagem", "arquivo_imagem"])
        w.writeheader()
        w.writerows(linhas)

    novo = not ARQ_USADOS.exists()
    with open(ARQ_USADOS, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["data", "termo", "achou"])
        if novo:
            w.writeheader()
        w.writerows(usados)

    print(f"\n{len(linhas)} oferta(s) prontas em {ARQ_SAIDA.name}. Próximo passo: python scripts/gerar_posts.py")


if __name__ == "__main__":
    main()
