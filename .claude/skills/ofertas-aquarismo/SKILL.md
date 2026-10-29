---
name: ofertas-aquarismo
description: Roda uma rodada completa de ofertas do Mercado Livre para o grupo de AQUARISMO do Lucas (busca, seleção, link de afiliado, imagem e envio à aba Aquarismo do Painel de Ofertas). Use quando o Lucas pedir /ofertas-aquarismo, "roda as ofertas de aquarismo" ou uma rodada de aquário.
---

# /ofertas-aquarismo: rodada completa de ofertas de aquarismo

Mesmo processo e mesmos critérios da skill `ofertas-hof` (dentistas), mas com
termos, marcas, histórico e aba próprios do aquarismo.

Argumento opcional: número de ofertas da rodada (padrão 10). Ex.: `/ofertas-aquarismo 5`.
O Lucas está aprendendo: no fim, explique em português simples o que saiu.
Fale pouco durante a execução; use a lista de tarefas para mostrar o progresso.

## A regra de ouro deste nicho

TODO comando Python roda com `NICHO=aquarismo` na frente. É isso que faz os scripts
usarem `config/aquarismo/` e `dados/aquarismo/` (termos, marcas, histórico e rodízio
do aquarismo) e mandarem os posts para a aba **Aquarismo** do painel, com 🐠.
Sem o `NICHO=aquarismo`, o script mexe nos dados de odontologia: não esqueça.

## 0. Preparar o projeto

- Repositório: `lucaasmacedo/ofertas-dentistas` em `/home/claude/ofertas-dentistas`.
  Se não existir, anexar com add_repo (access: push) e clonar. Se existir: `git pull`.
- Ler o `CLAUDE.md` do repositório (painel, seletores do site, lições aprendidas).
- Painel: https://claude.ai/artifact/Y9W5arBiM793MoBdtsEAiR (coleção `ofertas`, aba Aquarismo).

## 1. Sincronizar o que o Lucas marcou no painel

- ArtifactData `list` da coleção `ofertas` com `out_dir` = `<scratchpad>/painel_export`.
- `NICHO=aquarismo python scripts/sincronizar_historico.py <scratchpad>/painel_export`
  (só lê os posts da aba Aquarismo).

## 2. Escolher os termos (rodízio)

- `NICHO=aquarismo python scripts/escolher_termos.py <N>` -> `dados/aquarismo/rodada/termos.json`
- Os termos ficam em `config/aquarismo/nichos.csv` (o Lucas edita no Excel).

## 3. Buscar no navegador (Claude in Chrome)

- Navegador: o Chrome logado na conta de afiliado do **Lucas**. Hoje são dois:
  Windows "Afiliados" (deviceId 18191268-9a65-4204-bf69-90f2f9c76cbd) ou o perfil do Lucas
  no Mac (b91e9944-43f1-405f-b54d-b2e2e4e29ee0). NUNCA o perfil do Mac logado como
  "Leandro" (92969a82-be35-4e9e-b166-97b892b1768f). Na primeira busca, conferir que o
  usuário logado é "Lucas"; se não for, parar e avisar.
- Mesmo método da skill ofertas-hof: `navigate` para `url_busca`, wait 2s, `javascript_tool`
  com `const P = {...}` + `scripts/navegador/buscar.js`.
- Lição aprendida: no máximo 3 ou 4 termos por `browser_batch` (lotes maiores estouram o
  tempo e a ferramenta pode continuar rodando em segundo plano, bagunçando a aba).
  Dica: na 1ª busca, guardar a função em `sessionStorage` e reaproveitar nas seguintes
  (vale por domínio: lista., www. e produto. são separados).
- Gravar `dados/aquarismo/rodada/candidatos.json` no formato `{ "<termo>": <json devolvido> }`.

## 4. Curadoria (o "olho de aquarista")

Antes de selecionar, revisar o `top` de cada termo e tirar o que não serve. Reordenar se
o melhor produto não estiver em primeiro:
- Fora do tema: produto que só tem a palavra no título (ex.: "carvão" de churrasco,
  "bomba" de piscina, ração de cachorro, aquário de decoração/vaso, LED de quarto).
- Especificação errada para o termo (ex.: teste de pH quando o termo é amônia; filtro
  canister quando o termo é hang-on). Não tratar como equivalentes.
- Anúncio importado (código CBT) sem frete grátis e sem vendas: descartar.
- Repetição: o mesmo produto sugerido há menos de 2 dias só volta se o preço caiu.
- NUNCA buscar ou postar: animais vivos (peixes, camarões, caramujos, plantas vivas
  importadas sem nota), medicamentos veterinários e antibióticos (remédio para peixe,
  "cura ictio", verde malaquita etc.): são regulados.

## 5. Selecionar e mandar baixar as imagens

- `NICHO=aquarismo python scripts/selecionar_ofertas.py`
  -> `dados/aquarismo/rodada/selecionadas.json` e `dados/imagens_pendentes.csv` (a lista de
  imagens é a mesma dos dois nichos: é ela que dispara o robô do GitHub).
- Commit + push de `dados/imagens_pendentes.csv`. Guardar o horário do push.

## 6. Links de afiliado (enquanto o robô baixa as imagens)

- Para cada oferta: `navigate` para `url_produto` (NUNCA clicar nos links click1), wait 2s,
  `javascript_tool` com `scripts/navegador/link_afiliado.js` (ou a versão que também lê
  comissão "GANHOS X%", estoque e Full, como nas rodadas de odontologia).
- Critérios obrigatórios (iguais aos de odontologia):
  - anúncio ativo e com "Estoque disponível"; se não confirmar, tentar a 2ª opção do termo;
  - Full só se aparecer "Armazenado e enviado pelo Full";
  - comissão: ler a barra de Afiliados; se não aparecer, "não informada" (nunca presumir);
  - cupom só se testado; sem link de afiliado a oferta NÃO vai.
- Específico de aquarismo: conferir litragem indicada, vazão (L/h), potência (W) e
  **voltagem** (110 V, 220 V ou bivolt) dos equipamentos. Se o anúncio tiver variações de
  voltagem, avisar o Lucas para conferir na hora de postar.
- Gravar `dados/aquarismo/rodada/links.json` no formato `{ "<id_anuncio>": <json devolvido> }`.
- Fechar a aba (`tabs_close_mcp`). Se "Compartilhar" não aparecer em TODOS: conta de afiliado
  deslogada, parar e avisar.

## 7. Pegar as imagens

- Esperar a execução do `baixar-imagens.yml` criada depois do push:
  `gh api "repos/lucaasmacedo/ofertas-dentistas/actions/workflows/baixar-imagens.yml/runs?per_page=1"`
- `git clone --depth 1 -b imagens https://github.com/lucaasmacedo/ofertas-dentistas <scratchpad>/imagens`

## 8. Montar e gerar os posts

- `NICHO=aquarismo python scripts/montar_rodada.py <scratchpad>/imagens`
  Sinal de confiança no aquarismo (Anvisa não se aplica): marca da lista
  `config/aquarismo/marcas_confiaveis.csv` OU loja oficial. Sem nenhum dos dois, a oferta
  das categorias de `config/aquarismo/nicho.json` (`exige_confianca`) fica de fora.
- `NICHO=aquarismo python scripts/gerar_posts.py` -> `saida/aquarismo/AAAA-MM-DD/HHhMM/`
- Revisar `posts.txt`: limpar títulos cortados ou com "|" no fim (corrigir no `painel/NN.json`
  e no `posts.txt`) e não fazer alegações que o anúncio não sustenta.

## 9. Enviar ao Painel de Ofertas (aba Aquarismo)

- Subir os .jpg da pasta da rodada: Artifact publish com `url` do painel, `asset: true`,
  `file_paths` (até 25 por chamada).
- Gravar `<scratchpad>/mapa.json` = `{ "<nome do .jpg>": "<id do asset>" }`.
- `NICHO=aquarismo python scripts/preparar_painel.py <pasta>/painel <scratchpad>/mapa.json`
  -> doc_id com prefixo `aquarismo_` e campo `especialidade: "Aquarismo"`.
- ArtifactData `batch` com um `set` por post (`collection: ofertas`, `file_path` ABSOLUTO).

## 10. Salvar e contar

- Commit + push de `dados/aquarismo/historico.csv`, `dados/aquarismo/termos_usados.csv`,
  `dados/aquarismo/ofertas_rodada.csv`.
- Responder ao Lucas, curto, com uma tabela: produto, preço, Full, comissão; depois o que
  ficou de fora e por quê; e se algum termo não acha nada há várias rodadas (ver
  `dados/aquarismo/termos_usados.csv`), sugerir trocar ou pausar em `config/aquarismo/nichos.csv`.
