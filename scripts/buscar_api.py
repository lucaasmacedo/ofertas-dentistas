"""
Busca as ofertas pela API pública do Mercado Livre (sem navegador).
Roda no GitHub Actions (que tem internet liberada), igual ao robô de imagens.

Entrada:  dados/busca_pendente.json  (cópia de dados/rodada/termos.json)
Saída:    pasta busca_resultado/ com
            candidatos.json  -> MESMO formato que o buscar.js devolvia no navegador
                                { "<termo>": {"anuncios", "aprovados", "top": [[...]]} }
            log.txt          -> o que aconteceu em cada termo (para conferir)

Cada item do "top" é uma lista:
  [id, titulo, preco_de, preco_por, desconto_pct, so_pix, vendidos, full, frete_gratis, imagem, tipo]
(assim o selecionar_ofertas.py continua funcionando sem mudança)

Chave da API (opcional): se o Mercado Livre exigir login de desenvolvedor,
o token vem da variável de ambiente ML_TOKEN (guardada nos "Secrets" do
GitHub, NUNCA no código).
"""

import json
import math
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ENTRADA = PASTA_PROJETO / "dados" / "busca_pendente.json"
SAIDA = PASTA_PROJETO / "busca_resultado"
TOP = 8  # quantos candidatos guardar por termo (mais opções = menos repetição)


def chamar_api(termo):
    """Pede à API os 50 primeiros anúncios do termo. Devolve (dados, erro)."""
    url = ("https://api.mercadolibre.com/sites/MLB/search?"
           + urllib.parse.urlencode({"q": termo, "limit": 50}))
    cabecalho = {"User-Agent": "ofertas-dentistas/1.0", "Accept": "application/json"}
    if os.environ.get("ML_TOKEN"):
        cabecalho["Authorization"] = "Bearer " + os.environ["ML_TOKEN"]
    try:
        pedido = urllib.request.Request(url, headers=cabecalho)
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return json.loads(resposta.read()), None
    except urllib.error.HTTPError as erro:
        return None, f"HTTP {erro.code}: {erro.read()[:300].decode('utf-8', 'ignore')}"
    except Exception as erro:  # sem internet, tempo esgotado etc.
        return None, str(erro)


# ---- Relevância: mesma regra do buscar.js -------------------------------
def normalizar(texto):
    t = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)              # 4,5 -> 4.5
    t = re.sub(r"(\d)\s+(ml|mm|g|cm|un|l)\b", r"\1\2", t)  # 1 ml -> 1ml
    t = re.sub(r"\b0+(\d)", r"\1", t)                   # 01ml -> 1ml
    return t


def relevante(titulo, chaves):
    n = normalizar(titulo)
    produto = normalizar(chaves.get("produto", "")).rstrip("s")
    if produto and produto not in n:
        return False
    medidas = chaves.get("medidas", [])
    if not medidas:
        return True
    # a medida precisa estar "sozinha": 1ml casa com 1ml, mas não com 21ml
    return any(re.search(r"(^|[^0-9.])" + re.escape(normalizar(m)) + r"(?![0-9])", n)
               for m in medidas)


def miolo_imagem(url):
    """Pega só o miolo do nome da foto (o resto o robô de imagens monta)."""
    m = re.search(r"(\d+-ML[A-Z]\d+_\d+)", url or "")
    return m.group(1) if m else ""


def converter(item):
    """Transforma um anúncio da API no formato compacto do buscar.js."""
    por = item.get("price") or 0
    de = item.get("original_price") or por
    desc = round((1 - por / de) * 100) if de and por and de > por else 0
    envio = item.get("shipping") or {}
    return {
        "id": item.get("id", ""),
        "titulo": (item.get("title") or "")[:90],
        "de": de, "por": por, "desc": desc,
        "pix": 0,  # a API não diz se o desconto é só no Pix
        "vendidos": item.get("sold_quantity") or 0,
        "full": 1 if envio.get("logistic_type") == "fulfillment" else 0,
        "frete": 1 if envio.get("free_shipping") else 0,
        "miolo": miolo_imagem(item.get("thumbnail", "")),
        "tipo": "i",  # sempre o anúncio (MLB-...), que abre direto no produto certo
    }


def nota(x):
    """Desconto pesa mais; vendidos e envio Full/grátis desempatam (igual ao buscar.js)."""
    return x["desc"] + min(15, math.log10(1 + x["vendidos"]) * 4) + x["full"] * 3 + x["frete"] * 2


def main():
    termos = json.loads(ENTRADA.read_text(encoding="utf-8"))
    SAIDA.mkdir(exist_ok=True)
    candidatos, log, erros = {}, [], 0

    for t in termos:
        dados, erro = chamar_api(t["termo"])
        if erro:
            erros += 1
            log.append(f"ERRO  {t['termo']}: {erro}")
            candidatos[t["termo"]] = {"anuncios": 0, "aprovados": 0, "top": [], "erro": erro}
            continue
        itens, vistos = [], set()
        for bruto in dados.get("results", []):
            x = converter(bruto)
            if x["id"] and x["por"] and x["id"] not in vistos:
                vistos.add(x["id"])
                itens.append(x)
        ok = [x for x in itens
              if x["desc"] >= t["desconto_min"]
              and t["preco_min"] <= x["por"] <= t["preco_max"]
              and x["miolo"] and relevante(x["titulo"], t["chaves"])]
        ok.sort(key=nota, reverse=True)
        top = [[x["id"], x["titulo"], x["de"], x["por"], x["desc"], x["pix"], x["vendidos"],
                x["full"], x["frete"], x["miolo"], x["tipo"]] for x in ok[:TOP]]
        candidatos[t["termo"]] = {"anuncios": len(itens), "aprovados": len(ok), "top": top}
        log.append(f"ok    {t['termo']}: {len(itens)} anúncios, {len(ok)} aprovados")

    (SAIDA / "candidatos.json").write_text(
        json.dumps(candidatos, ensure_ascii=False, indent=1), encoding="utf-8")
    (SAIDA / "log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    if termos and erros == len(termos):
        sys.exit(1)  # nenhum termo funcionou: marca a execução como erro


if __name__ == "__main__":
    main()
