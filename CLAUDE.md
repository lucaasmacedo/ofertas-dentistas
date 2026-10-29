# Ofertas Dentistas

Robô de ofertas do Mercado Livre para um grupo de WhatsApp de dentistas
(boa parte trabalha com HOF - Harmonização Orofacial). O Lucas posta as ofertas
com link de afiliado.

## Como o projeto funciona (modelo híbrido)

- **Navegador (extensão Claude in Chrome, perfil "Afiliados")**: encontrar ofertas
  no site do Mercado Livre e gerar o link de afiliado (não existe API pública
  para links de afiliado).
- **Código (este repositório)**: tudo que é regra e repetição: histórico,
  filtros, texto do post, imagem, organização dos arquivos.

## Estrutura

- `dados/historico.csv` - todas as ofertas já sugeridas. Toda oferta entregue
  entra como "sugerida"; o Lucas só avisa quando NÃO publicou alguma.
- `dados/` - entradas e saídas de cada rodada.
- `scripts/` - código Python.
- `saida/AAAA-MM-DD/HHhMM/` - posts prontos (posts.txt + imagens) de cada rodada.
  Não vai para o GitHub.
- `scripts/gerar_posts.py` - aplica as regras e gera os posts. `--simular` testa
  sem gravar no histórico.
- `dados/ofertas_rodada.csv` - entrada da rodada (preenchida pela etapa do
  navegador). Formato de exemplo em `dados/exemplo_ofertas.csv`.

## Painel de Ofertas (onde o Lucas vê os posts)

- Página privada: https://claude.ai/artifact/Y9W5arBiM793MoBdtsEAiR
  (código em `painel/index.html`; republicar sempre neste mesmo link).
- Os posts ficam no banco do painel, coleção `ofertas`, um documento por post
  (id `AAAA-MM-DD_HHhMM_NN`). Campos: data, rodada, ordem, id_anuncio, titulo,
  categoria, preco_de, preco_por, desconto_pct, texto, link_afiliado,
  imagem_asset, status (sugerida | publicada | nao_publicada), exemplo.
- Imagens sobem para os assets do painel; o documento guarda o id em `imagem_asset`.
- Os botões "Publiquei" / "Não publiquei" mudam o `status`. Ao fim do dia,
  sincronizar esses status de volta para `dados/historico.csv`.
- Documentos com `exemplo: true` são de demonstração e podem ser apagados.
- **Especialidades (abas do painel):** cada post tem o campo `especialidade`
  (padrão "Dentistas e HOF"; posts antigos sem o campo contam como essa). A lista
  de abas fica na constante `ESPECIALIDADES` em `painel/index.html` (hoje:
  "Dentistas e HOF", "Aquarismo"). Para enviar uma rodada de outra especialidade:
  `python scripts/preparar_painel.py <pasta>/painel <mapa.json> "Aquarismo"`
  (o doc_id ganha o prefixo `aquarismo_` para não colidir com outras abas).

## Nichos (o que buscar)

- `config/nichos.csv` define o que a etapa do navegador busca: só linhas com
  `ativo = sim`, começando pela prioridade alta. Cada linha tem termo de busca,
  desconto mínimo (%) e faixa de preço (R$). O Lucas edita esse arquivo
  (abre no Excel) para mudar o foco, sem mexer em código.
- Foco do grupo: itens de GIRO (recompra frequente), principalmente de HOF:
  agulhas, cânulas, seringas, conectores, descartáveis, antissepsia.
  A lista pode ser grande; a prioridade é que define o que sai mais.
- Prioridade = peso no rodízio de cada rodada: ~60% das ofertas de
  prioridade alta (giro), ~30% média, ~10% baixa (equipamentos e afins).
  Dentro de cada prioridade, começar pelos termos há mais tempo sem oferta.
- Volume: se um termo trouxer poucas ofertas na busca, avisar o Lucas para
  pausar (ativo = nao). Linhas pausadas não são apagadas.
- Nunca buscar produtos regulados ou de venda restrita (toxina botulínica,
  preenchedores/ácido hialurônico injetável, bioestimuladores, fios de
  sustentação, anestésicos, medicamentos).
- Produto de uso profissional (dispositivo médico) precisa de pelo menos UM
  sinal de confiança: anúncio cita a Anvisa, OU marca da lista
  `config/marcas_confiaveis.csv` (o Lucas edita), OU vendido por loja oficial.
  Sem nenhum desses, pular: a Anvisa já multou o próprio Mercado Livre por
  anúncios de produtos sem registro.
- Sem link de afiliado, a oferta NUNCA vai para o painel.

## Como fazer uma rodada (passo a passo para o Claude)

0. Ler `config/nichos.csv`.
1. Preencher `dados/ofertas_rodada.csv` (etapa do navegador). Imagem pela
   coluna `url_imagem` ou, se já salva, pelo caminho em `arquivo_imagem`.
   Atenção: o ambiente na nuvem não acessa os servidores de imagem do
   Mercado Livre (bloqueio de rede); a imagem precisa chegar por outro caminho.
2. `python scripts/gerar_posts.py` -> gera `saida/AAAA-MM-DD/HHhMM/` com
   `painel/NN.json` (um por post) e as imagens.
3. Subir as imagens como assets do painel (Artifact, `asset: true`).
4. Para cada `painel/NN.json`: tirar `doc_id` e `imagem_arquivo`, pôr
   `imagem_asset` com o id devolvido, e gravar em `ofertas/<doc_id>` (batch).
5. Commit + push do `dados/historico.csv`.

## Etapa do navegador (aprendido no reconhecimento de 20/10/2026)

- Busca: abrir `https://lista.mercadolivre.com.br/<termo-com-hifens>`.
  Cada anúncio é um `.poly-card`. Extrair com javascript_tool:
  título (`a.poly-component__title`), preço atual (`.poly-price__current`),
  preço antigo (`s.andes-money-amount--previous`), frações em
  `.andes-money-amount__fraction` + `.andes-money-amount__cents`,
  ID `MLB\d+` (no link ou no HTML do card), imagem (`img.poly-component__picture`).
  Texto "XX% OFF no Pix" => desconto só no Pix (coluna `so_pix = sim`).
- Links de busca podem ser rastreadores de anúncio (click1.mercadolivre...).
  NÃO clicar neles: abrir o produto pelo endereço montado a partir do código.
- Código + TIPO vêm do link do anúncio (buscar.js): `/p/MLB...` = catálogo
  (abre em `www.mercadolivre.com.br/p/MLB...`); `item_id:MLB...` ou `MLB-...` =
  anúncio comum (abre em `produto.mercadolivre.com.br/MLB-...`). NUNCA adivinhar
  o tipo pelo tamanho do número: catálogo também pode ter 10 dígitos
  (erro real em 20/10: abriu uma "Tampa de Óleo" no lugar de uma torneira).
- Trava: link_afiliado.js devolve o título da página e montar_rodada.py descarta
  a oferta se o título não bater com o escolhido.
- Alguns produtos não têm a barra de Afiliados (provavelmente fora do programa);
  link_afiliado.js espera o botão até 6s; se não aparecer, a oferta fica de fora.
- Link de afiliado: na página do produto, botão "Compartilhar" na barra de
  Afiliados (topo) abre "Gerar link / ID de produto"; ler o valor
  `https://meli.la/...` dos inputs. Gerar o link adiciona o produto em
  "Minhas recomendações" (normal). Fechar o painel com Escape.
- Imagens: o navegador baixa, mas a extensão bloqueia trazer a imagem para cá,
  e a nuvem do Claude não acessa mlstatic.com. Solução: GitHub Actions.
  1. Escrever `dados/imagens_pendentes.csv` (nome,url) e dar push.
  2. O workflow `baixar-imagens.yml` baixa, converte para JPG e grava no
     branch `imagens` (substituído a cada execução).
  3. `git clone --depth 1 -b imagens` e usar os arquivos em `arquivo_imagem`.
  Disparo manual: `gh api -X POST repos/lucaasmacedo/ofertas-dentistas/actions/workflows/baixar-imagens.yml/dispatches -f ref=main`
  (o `gh workflow run` não funciona aqui).

## Sincronizar o que foi publicado

1. Ler a coleção `ofertas` do painel com `out_dir` (um JSON por post).
2. `python scripts/sincronizar_historico.py <pasta>` -> atualiza os status.
3. Ofertas "nao_publicada" não contam para o intervalo de repetição.

## Regras de repetição (configuráveis no topo de gerar_posts.py)

- Mesmo produto só volta depois de 2 dias.
- Exceção: se o preço caiu desde a última vez, pode voltar antes.
- Máximo de 3 ofertas da mesma categoria por dia; máximo de 10 posts por rodada.

## Regras

- O Lucas está aprendendo a programar: explique cada passo em português simples.
- Toda oferta sai com a imagem do anúncio, baixada automaticamente.
- Evitar repetição excessiva, sem proibir repetir: um produto bom pode voltar
  depois de um intervalo mínimo (padrão: dia sim, dia não). O histórico serve
  para controlar esse intervalo, não para descartar para sempre.
- Nunca salvar senhas, tokens ou chaves no código. Usar variáveis de ambiente (`.env`).
- Código em Python, simples e comentado em português.
