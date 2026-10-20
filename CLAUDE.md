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

## Nichos (o que buscar)

- `config/nichos.csv` define o que a etapa do navegador busca: só linhas com
  `ativo = sim`, começando pela prioridade alta. Cada linha tem termo de busca,
  desconto mínimo (%) e faixa de preço (R$). O Lucas edita esse arquivo
  (abre no Excel) para mudar o foco, sem mexer em código.
- Nunca buscar produtos regulados ou de venda restrita (toxina botulínica,
  preenchedores/ácido hialurônico injetável, anestésicos, medicamentos).

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
