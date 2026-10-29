"""
Prepara os posts da rodada para o banco do Painel de Ofertas.

Depois que o Claude sobe as imagens no painel, ele recebe um id para cada
uma. Este script troca o caminho local da imagem por esse id e grava um
arquivo "enviar_NN.json" por post, pronto para gravar no banco.

Cada post também recebe o campo "especialidade" (a aba do painel onde ele
aparece). O padrão é "Dentistas e HOF". Para outras especialidades, o id do
post ganha um prefixo (ex.: "aquarismo_2026-10-29_10h30_01") para nunca
colidir com uma rodada de outra especialidade no mesmo horário.

Entradas:
  <pasta_painel>  -> saida/AAAA-MM-DD/HHhMM/painel (gerada pelo gerar_posts.py)
  <mapa.json>     -> { "<nome do arquivo da imagem>": "<id do asset>", ... }
  [especialidade] -> opcional, ex.: "Aquarismo"

Como rodar:
  python scripts/preparar_painel.py <pasta_painel> <mapa.json> ["Aquarismo"]
Saída: imprime "doc_id  caminho_do_enviar_NN.json" de cada post.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ESPECIALIDADE_PADRAO = "Dentistas e HOF"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nicho  # noqa: E402


def slug(texto):
    """'Aquarismo' -> 'aquarismo'; 'Pet Shop' -> 'pet-shop' (sem acentos)."""
    t = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def main():
    pasta = Path(sys.argv[1])
    mapa = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else {}
    especialidade = sys.argv[3] if len(sys.argv) > 3 else nicho.ESPECIALIDADE
    for arq in sorted(pasta.glob("[0-9][0-9].json")):
        doc = json.loads(arq.read_text(encoding="utf-8"))
        doc_id = doc.pop("doc_id")
        if especialidade != ESPECIALIDADE_PADRAO:
            doc_id = f"{slug(especialidade)}_{doc_id}"
        imagem = doc.pop("imagem_arquivo", None)
        doc["imagem_asset"] = mapa.get(Path(imagem).name) if imagem else None
        doc["especialidade"] = especialidade
        destino = pasta / f"enviar_{arq.stem}.json"
        destino.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        print(doc_id, destino)


if __name__ == "__main__":
    main()
