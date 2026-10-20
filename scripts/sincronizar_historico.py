"""
Sincroniza o histórico com o que o Lucas marcou no Painel de Ofertas.

No painel, cada post tem os botões "Publiquei" / "Não publiquei".
Este script lê esses status (exportados do banco do painel como arquivos
JSON, um por post) e atualiza a coluna "status" do dados/historico.csv.

Como rodar:
  python scripts/sincronizar_historico.py <pasta_com_os_json>

A pasta é gerada pelo Claude ao ler o banco do painel (coleção "ofertas").
Posts de exemplo (exemplo = true) são ignorados.
"""

import csv
import json
import sys
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQ_HISTORICO = PASTA_PROJETO / "dados" / "historico.csv"


def ler_status_do_painel(pasta):
    """Lê todos os JSON da pasta e devolve {(data, id_anuncio): status}."""
    status = {}
    for arquivo in Path(pasta).rglob("*.json"):
        doc = json.loads(arquivo.read_text(encoding="utf-8"))
        # A exportação pode vir "embrulhada" em {"data": {...}}
        campos = doc.get("data") if isinstance(doc.get("data"), dict) else doc
        if campos.get("exemplo"):
            continue
        chave = (campos.get("data"), campos.get("id_anuncio"))
        if all(chave):
            status[chave] = campos.get("status", "sugerida")
    return status


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/sincronizar_historico.py <pasta_com_os_json>")
        return

    status_painel = ler_status_do_painel(sys.argv[1])
    with open(ARQ_HISTORICO, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        colunas = leitor.fieldnames
        linhas = list(leitor)

    mudancas = 0
    for linha in linhas:
        novo = status_painel.get((linha["data"], linha["id_anuncio"]))
        if novo and novo != linha["status"]:
            print(f"  {linha['data']}  {linha['titulo'][:45]:45}  {linha['status']} -> {novo}")
            linha["status"] = novo
            mudancas += 1

    with open(ARQ_HISTORICO, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"\n{mudancas} status atualizado(s) no histórico.")


if __name__ == "__main__":
    main()
