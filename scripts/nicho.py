"""
Qual nicho (especialidade) a rodada está usando.

Os scripts leem a variável de ambiente NICHO:
  - vazia (padrão)   -> Dentistas e HOF: config/ e dados/ (como sempre foi)
  - NICHO=aquarismo  -> config/aquarismo/ e dados/aquarismo/

Cada nicho tem seu próprio arquivo de termos (nichos.csv), marcas confiáveis,
histórico, rodízio e pasta de saída. Assim um produto de aquarismo nunca
bloqueia (nem repete) um de odontologia, e vice-versa.

As preferências do nicho ficam em config/<nicho>/nicho.json, por exemplo:
  {"especialidade": "Aquarismo", "emoji": "🐠",
   "mostrar_anvisa": false, "exige_confianca": ["aquario-giro", ...]}

Exemplo (no terminal):
  NICHO=aquarismo python scripts/escolher_termos.py 10
"""

import json
import os
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
NICHO = os.environ.get("NICHO", "").strip().lower()

PASTA_CONFIG = PASTA_PROJETO / "config" / NICHO if NICHO else PASTA_PROJETO / "config"
PASTA_DADOS = PASTA_PROJETO / "dados" / NICHO if NICHO else PASTA_PROJETO / "dados"
PASTA_SAIDA = PASTA_PROJETO / "saida" / NICHO if NICHO else PASTA_PROJETO / "saida"
PASTA_RODADA = PASTA_DADOS / "rodada"

# A lista de imagens é sempre a mesma (é ela que dispara o robô do GitHub)
ARQ_IMAGENS = PASTA_PROJETO / "dados" / "imagens_pendentes.csv"

# Preferências padrão = Dentistas e HOF (como o projeto funcionava antes)
_PADRAO = {
    "especialidade": "Dentistas e HOF",
    "emoji": "🦷",
    "mostrar_anvisa": True,
    "exige_confianca": ["hof-giro", "hof-insumos", "descartaveis", "odonto",
                        "esterilizacao", "biosseguranca"],
}
_arq = PASTA_CONFIG / "nicho.json"
CFG = {**_PADRAO, **(json.loads(_arq.read_text(encoding="utf-8")) if _arq.exists() else {})}

ESPECIALIDADE = CFG["especialidade"]
EMOJI = CFG["emoji"]
MOSTRAR_ANVISA = bool(CFG["mostrar_anvisa"])
EXIGE_CONFIANCA = set(CFG["exige_confianca"])

if NICHO and not PASTA_CONFIG.exists():
    raise SystemExit(f"Nicho '{NICHO}' não existe: crie a pasta {PASTA_CONFIG}")
