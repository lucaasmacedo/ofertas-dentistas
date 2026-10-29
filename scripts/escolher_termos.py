"""
Escolhe quais termos de busca entram na rodada (o "rodízio").

Regras:
  - Só termos com ativo = sim em config/nichos.csv.
  - Pesos por prioridade: ~60% alta, ~30% média, ~10% baixa.
  - Dentro de cada prioridade, primeiro os termos há mais tempo sem uso
    (consulta dados/termos_usados.csv). Empate: ordem aleatória.

Como rodar:
  python scripts/escolher_termos.py          -> 10 termos (padrão)
  python scripts/escolher_termos.py 4        -> 4 termos

Saída: dados/rodada/termos.json (lista de termos com seus critérios).
"""

import csv
import json
import random
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import nicho  # pastas e preferências do nicho (NICHO=aquarismo, etc.)

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQ_NICHOS = nicho.PASTA_CONFIG / "nichos.csv"
ARQ_USADOS = nicho.PASTA_DADOS / "termos_usados.csv"
PASTA_RODADA = nicho.PASTA_RODADA

PESOS = {"alta": 0.6, "media": 0.3, "baixa": 0.1}


def ler_csv(caminho):
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def chaves(termo):
    """
    Palavras que o título do anúncio PRECISA ter para ser relevante:
      - a primeira palavra (o produto: seringa, agulha, microcanula...)
      - as medidas (palavras com número: 1ml, 22g, 50mm, 13x4,5...)
    Na busca, basta o título ter o produto e PELO MENOS UMA das medidas.
    """
    palavras = termo.lower().split()
    medidas = [p.replace(",", ".") for p in palavras if any(ch.isdigit() for ch in p)]
    return {"produto": palavras[0], "medidas": medidas}


def cotas(total):
    """Divide o total entre as prioridades (ex.: 10 -> alta 6, media 3, baixa 1)."""
    c = {p: int(total * peso) for p, peso in PESOS.items()}
    # o que sobrar do arredondamento vai para a prioridade alta
    c["alta"] += total - sum(c.values())
    return c


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    nichos = [n for n in ler_csv(ARQ_NICHOS) if n["ativo"].strip().lower() == "sim"]

    # Última data em que cada termo foi usado ("" = nunca)
    ultimo_uso = {}
    for u in ler_csv(ARQ_USADOS):
        ultimo_uso[u["termo"]] = max(ultimo_uso.get(u["termo"], ""), u["data"])

    escolhidos, sobra = [], 0
    for prioridade, cota in cotas(total).items():
        grupo = [n for n in nichos if n["prioridade"] == prioridade]
        random.shuffle(grupo)                                  # desempate aleatório
        grupo.sort(key=lambda n: ultimo_uso.get(n["termo_busca"], ""))  # nunca usados primeiro
        cota += sobra                                          # herda o que faltou antes
        escolhidos += grupo[:cota]
        sobra = max(0, cota - len(grupo))

    termos = [{
        "termo": n["termo_busca"],
        "chaves": chaves(n["termo_busca"]),
        "categoria": n["categoria"],
        "prioridade": n["prioridade"],
        "desconto_min": float(n["desconto_min"] or 0),
        "preco_min": float(n["preco_min"] or 0),
        "preco_max": float(n["preco_max"] or 1e9),
        "url_busca": "https://lista.mercadolivre.com.br/" + "-".join(n["termo_busca"].replace(",", "-").split()),
    } for n in escolhidos]

    PASTA_RODADA.mkdir(parents=True, exist_ok=True)
    (PASTA_RODADA / "termos.json").write_text(json.dumps(termos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(termos)} termos escolhidos:")
    for t in termos:
        print(f"  [{t['prioridade']:5}] {t['termo']}  (último uso: {ultimo_uso.get(t['termo'], 'nunca')})")


if __name__ == "__main__":
    main()
