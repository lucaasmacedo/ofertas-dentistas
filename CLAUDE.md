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
- `saida/` - posts prontos (texto + imagem) de cada rodada. Não vai para o GitHub.

## Regras

- O Lucas está aprendendo a programar: explique cada passo em português simples.
- Toda oferta sai com a imagem do anúncio, baixada automaticamente.
- Evitar repetição excessiva, sem proibir repetir: um produto bom pode voltar
  depois de um intervalo mínimo (padrão: dia sim, dia não). O histórico serve
  para controlar esse intervalo, não para descartar para sempre.
- Nunca salvar senhas, tokens ou chaves no código. Usar variáveis de ambiente (`.env`).
- Código em Python, simples e comentado em português.
