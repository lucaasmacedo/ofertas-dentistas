"""
Escolhe a melhor oferta de cada termo, a partir do que o navegador encontrou.

Entradas:
  dados/rodada/termos.json      -> termos da rodada (escolher_termos.py)
  dados/rodada/candidatos.json  -> resultado do buscar.js para cada termo:
      { "<termo>": {"anuncios": 68, "aprovados": 21, "top": [[...], ...]}, ... }
  dados/historico.csv           -> para respeitar as regras de repetição

Regras:
  - pula títulos com produtos proibidos (toxina, preenchedor etc.)
  - pula produto já escolhido nesta rodada
  - respeita intervalo de repetição / exceção por queda de preço
  - fica com o primeiro que passar (o top já vem ordenado pelo navegador)

Saídas:
  dados/rodada/selecionadas.json -> ofertas escolhidas, com endereço do produto
  dados/imagens_pendentes.csv    -> lista para o robô do GitHub baixar as imagens
"""

import csv
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_posts import ARQ_HISTORICO, ler_csv, pode_postar  # reaproveita as regras

PASTA_PROJETO = Path(__file__).resolve().parent.parent
import nicho  # noqa: E402
PASTA_RODADA = nicho.PASTA_RODADA
ARQ_IMAGENS = nicho.ARQ_IMAGENS

# Produtos regulados que nunca entram (o título é comparado sem acentos).
# Atenção: "preenchimento" sozinho NÃO entra aqui, porque cânulas e seringas
# "para preenchimento" são permitidas; o proibido é o preenchedor em si.
PROIBIDOS = [
    "toxina", "botulin", "preenchedor",
    "bioestimulador", "hidroxiapatita", "polilatico", "policaprolactona",
    "fio de pdo", "fios de pdo", "fio pdo", "fios de sustentacao",
    "anestesico", "lidocaina", "articaina", "mepivacaina", "prilocaina",
    "acido hialuronico injetavel",
]


def sem_acento(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def proibido(titulo):
    t = sem_acento(titulo)
    return next((p for p in PROIBIDOS if p in t), None)


def url_produto(id_anuncio, tipo):
    """
    tipo "p" = produto de catálogo -> www.mercadolivre.com.br/p/MLB...
    tipo "i" = anúncio comum       -> produto.mercadolivre.com.br/MLB-...
    (O tipo vem do próprio link do anúncio na busca; o tamanho do número
    NÃO serve para adivinhar, porque catálogos também podem ter 10 dígitos.)
    """
    if tipo == "p":
        return f"https://www.mercadolivre.com.br/p/{id_anuncio}"
    return f"https://produto.mercadolivre.com.br/MLB-{id_anuncio[3:]}"


def main():
    termos = json.loads((PASTA_RODADA / "termos.json").read_text(encoding="utf-8"))
    candidatos = json.loads((PASTA_RODADA / "candidatos.json").read_text(encoding="utf-8"))
    historico = ler_csv(ARQ_HISTORICO)
    hoje = date.today()

    escolhidas, usados = [], set()
    for t in termos:
        resultado = candidatos.get(t["termo"], {})
        top = resultado.get("top", [])
        if not top:
            print(f"✖ {t['termo']}: nenhum anúncio passou nos critérios "
                  f"({resultado.get('anuncios', 0)} anúncios na busca)")
            continue
        for item in top:
            id_, titulo, de, por, desc, pix, vendidos, full, frete, miolo = item[:10]
            tipo = item[10] if len(item) > 10 else "i"
            motivo_proibido = proibido(titulo)
            if motivo_proibido:
                print(f"   pulado (proibido: {motivo_proibido}): {titulo[:60]}")
                continue
            if id_ in usados:
                continue
            ok, motivo = pode_postar({"id_anuncio": id_, "preco_por": str(por)}, historico, hoje)
            if not ok:
                print(f"   pulado ({motivo}): {titulo[:60]}")
                continue
            usados.add(id_)
            escolhidas.append({
                "termo": t["termo"], "categoria": t["categoria"],
                "desconto_min": t["desconto_min"],
                "id_anuncio": id_, "titulo": titulo, "preco_de": de, "preco_por": por,
                "desconto_pct": desc, "so_pix": bool(pix), "vendidos": vendidos,
                "full": bool(full), "frete_gratis": bool(frete),
                "url_imagem": f"https://http2.mlstatic.com/D_Q_NP_2X_{miolo}-E.webp",
                "url_produto": url_produto(id_, tipo),
            })
            print(f"✔ {t['termo']}: {titulo[:55]}  R$ {por:.2f} ({desc}% OFF)")
            break
        else:
            print(f"✖ {t['termo']}: candidatos existem, mas todos foram pulados")

    (PASTA_RODADA / "selecionadas.json").write_text(
        json.dumps(escolhidas, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(ARQ_IMAGENS, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nome", "url"])
        for e in escolhidas:
            w.writerow([e["id_anuncio"], e["url_imagem"]])

    print(f"\n{len(escolhidas)} oferta(s) selecionada(s). Próximo passo: gerar os links de afiliado.")
    for e in escolhidas:
        print(f"  {e['id_anuncio']}  {e['url_produto']}")


if __name__ == "__main__":
    main()
