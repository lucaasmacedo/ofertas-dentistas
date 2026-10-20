"""
Prepara os posts da rodada para o banco do Painel de Ofertas.

Depois que o Claude sobe as imagens no painel, ele recebe um id para cada
uma. Este script troca o caminho local da imagem por esse id e grava um
arquivo "enviar_NN.json" por post, pronto para gravar no banco.

Entradas:
  <pasta_painel>  -> saida/AAAA-MM-DD/HHhMM/painel (gerada pelo gerar_posts.py)
  <mapa.json>     -> { "<nome do arquivo da imagem>": "<id do asset>", ... }

Como rodar:
  python scripts/preparar_painel.py <pasta_painel> <mapa.json>
Saída: imprime "doc_id  caminho_do_enviar_NN.json" de cada post.
"""

import json
import sys
from pathlib import Path


def main():
    pasta = Path(sys.argv[1])
    mapa = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else {}
    for arq in sorted(pasta.glob("[0-9][0-9].json")):
        doc = json.loads(arq.read_text(encoding="utf-8"))
        doc_id = doc.pop("doc_id")
        imagem = doc.pop("imagem_arquivo", None)
        doc["imagem_asset"] = mapa.get(Path(imagem).name) if imagem else None
        destino = pasta / f"enviar_{arq.stem}.json"
        destino.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        print(doc_id, destino)


if __name__ == "__main__":
    main()
