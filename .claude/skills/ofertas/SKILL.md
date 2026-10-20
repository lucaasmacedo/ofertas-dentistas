---
name: ofertas
description: Roda uma rodada completa de ofertas do Mercado Livre para o grupo de dentistas/HOF do Lucas (busca, seleção, link de afiliado, imagem e envio ao Painel de Ofertas). Use quando o Lucas pedir /ofertas, "roda as ofertas" ou uma nova rodada.
---

# /ofertas: rodada completa de ofertas

Argumento opcional: número de ofertas da rodada (padrão 10). Ex.: `/ofertas 5`.
O Lucas está aprendendo: no fim, explique em português simples o que saiu.
Fale pouco durante a execução; use a lista de tarefas para mostrar o progresso.

## 0. Preparar o projeto

- Repositório: `lucaasmacedo/ofertas-dentistas` em `/home/claude/ofertas-dentistas`.
  Se não existir, anexar com add_repo (access: push) e clonar. Se existir: `git pull`.
- Ler o `CLAUDE.md` do repositório (regras, painel, seletores do site).
- Painel: https://claude.ai/artifact/Y9W5arBiM793MoBdtsEAiR (coleção `ofertas`).

## 1. Sincronizar o que o Lucas marcou no painel

- ArtifactData `list` da coleção `ofertas` com `out_dir` = `<scratchpad>/painel_export`.
- `python scripts/sincronizar_historico.py <scratchpad>/painel_export`

## 2. Escolher os termos (rodízio)

- `python scripts/escolher_termos.py <N>` -> `dados/rodada/termos.json`

## 3. Buscar no navegador (Claude in Chrome)

- Carregar as ferramentas do Chrome numa só ToolSearch (tabs_context_mcp, tabs_create_mcp,
  navigate, computer, javascript_tool, tabs_close_mcp). `tabs_context_mcp` e abrir uma aba nova.
- Se o Chrome não responder: parar e pedir ao Lucas para abrir o Chrome com a extensão.
- Para cada termo de `termos.json`:
  1. `navigate` para `url_busca`; `computer wait` 2s.
  2. `javascript_tool` com a linha
     `const P = {desconto_min, preco_min, preco_max, chaves};` (valores do termo)
     seguida do conteúdo de `scripts/navegador/buscar.js`.
  3. Guardar o JSON devolvido.
- Gravar tudo em `dados/rodada/candidatos.json` no formato `{ "<termo>": <json devolvido> }`.

## 4. Selecionar e mandar baixar as imagens

- `python scripts/selecionar_ofertas.py` -> `selecionadas.json` e `dados/imagens_pendentes.csv`.
- Commit + push de `dados/imagens_pendentes.csv` (dispara o robô do GitHub que baixa as imagens).
  Guardar o horário do push para achar a execução certa depois.

## 5. Links de afiliado (enquanto o robô baixa as imagens)

- Para cada oferta de `selecionadas.json`:
  1. `navigate` para `url_produto` (NUNCA clicar nos links click1 da busca); wait 2s.
  2. `javascript_tool` com o conteúdo de `scripts/navegador/link_afiliado.js`.
- Gravar `dados/rodada/links.json` no formato `{ "<id_anuncio>": <json devolvido> }`.
- Fechar a aba criada (`tabs_close_mcp`).
- Se der "botão Compartilhar não encontrado" em TODOS: avisar que a conta de afiliado
  pode estar deslogada no Chrome e parar. Em um ou outro: produto fora do programa,
  segue sem ele (não ficar recarregando).
- Guardar também o `titulo` devolvido: o montar_rodada.py usa para conferir se a
  página aberta era mesmo do produto escolhido.

## 6. Pegar as imagens

- Esperar a execução do workflow `baixar-imagens.yml` criada depois do push:
  `gh api "repos/lucaasmacedo/ofertas-dentistas/actions/workflows/baixar-imagens.yml/runs?per_page=1"`
  (checar status a cada ~6s até `completed`). `gh workflow run`/`gh run watch` não funcionam aqui.
- `git clone --depth 1 -b imagens https://github.com/lucaasmacedo/ofertas-dentistas <scratchpad>/imagens`

## 7. Montar e gerar os posts

- `python scripts/montar_rodada.py <scratchpad>/imagens`
- `python scripts/gerar_posts.py` -> `saida/AAAA-MM-DD/HHhMM/` (posts.txt, imagens, painel/NN.json)

## 8. Enviar ao Painel de Ofertas

- Subir as imagens da pasta da rodada: Artifact publish com `url` do painel, `asset: true`,
  `file_paths` = os .jpg da pasta (até 25 por chamada).
- Gravar `<scratchpad>/mapa.json` = `{ "<nome do .jpg>": "<id do asset>" }`.
- `python scripts/preparar_painel.py <pasta>/painel <scratchpad>/mapa.json`
  -> imprime `doc_id caminho`. ArtifactData `batch` com um `set` por post
  (`collection: ofertas`, `doc_id`, `file_path` com o caminho ABSOLUTO).

## 9. Salvar e contar

- Commit + push (`dados/historico.csv`, `dados/termos_usados.csv`, `dados/ofertas_rodada.csv`).
- Responder ao Lucas, curto:
  - quantos posts foram para o painel (rodada `HHhMM`);
  - o que ficou de fora e por quê (sem oferta, repetição, sem Anvisa, sem link);
  - se um termo não acha nada há várias rodadas (ver `dados/termos_usados.csv`),
    sugerir pausar em `config/nichos.csv`.
