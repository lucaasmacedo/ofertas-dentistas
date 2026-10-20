"""
Gerador de posts de ofertas para o grupo de dentistas.

O que ele faz, em ordem:
  1. Lê as ofertas encontradas na rodada (dados/ofertas_rodada.csv),
     que vêm da etapa do navegador.
  2. Lê o histórico (dados/historico.csv) para controlar repetição.
  3. Aplica as regras: intervalo mínimo, exceção por queda de preço
     e limite por categoria.
  4. Para cada oferta aprovada: monta o texto do post e pega a imagem
     (baixa pela coluna url_imagem ou copia o arquivo da coluna arquivo_imagem).
  5. Salva tudo em saida/AAAA-MM-DD/HHhMM/:
       posts.txt          -> todos os textos, para leitura rápida
       NN_<id>.jpg        -> imagens
       painel/NN.json     -> um arquivo por post, pronto para o Painel de Ofertas
  6. Registra no histórico como "sugerida".

Como rodar (dentro da pasta do projeto):
  python scripts/gerar_posts.py            -> rodada de verdade
  python scripts/gerar_posts.py --simular  -> testa sem gravar no histórico
"""

import csv
import json
import shutil
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------
# CONFIGURAÇÕES (mude aqui quando quiser ajustar as regras)
# ---------------------------------------------------------------
INTERVALO_DIAS = 2         # mesmo produto só volta depois de X dias
MAX_POR_CATEGORIA = 3      # máximo de ofertas da mesma categoria por dia
MAX_POSTS_POR_RODADA = 10  # máximo de posts gerados por rodada

# Caminhos dos arquivos (a pasta do projeto é a "mãe" da pasta scripts)
PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQ_OFERTAS = PASTA_PROJETO / "dados" / "ofertas_rodada.csv"
ARQ_HISTORICO = PASTA_PROJETO / "dados" / "historico.csv"
PASTA_SAIDA = PASTA_PROJETO / "saida"

COLUNAS_HISTORICO = [
    "data", "id_anuncio", "titulo", "categoria",
    "preco_de", "preco_por", "desconto_pct", "link_afiliado", "status",
]


# ---------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------
def ler_csv(caminho):
    """Lê um CSV e devolve uma lista de dicionários (uma linha = um dicionário)."""
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def para_numero(texto):
    """Converte preço em texto ('1.299,90' ou '1299.90') para número."""
    texto = str(texto).strip().replace("R$", "").replace(" ", "")
    if "," in texto:  # formato brasileiro: 1.299,90
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto) if texto else 0.0


def formatar_reais(valor):
    """Converte 1299.9 em 'R$ 1.299,90'."""
    texto = f"{valor:,.2f}"  # 1,299.90 (padrão americano)
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ultima_aparicao(historico, id_anuncio):
    """
    Procura a última vez que o produto apareceu no grupo.
    Ofertas marcadas como "nao_publicada" não contam: o grupo nunca as viu.
    """
    vezes = [h for h in historico
             if h["id_anuncio"] == id_anuncio and h.get("status") != "nao_publicada"]
    if not vezes:
        return None
    return max(vezes, key=lambda h: h["data"])  # datas AAAA-MM-DD ordenam certo


def pode_postar(oferta, historico, hoje):
    """
    Decide se a oferta pode sair hoje. Devolve (sim/não, motivo).
    Regra 1: produto novo sempre pode.
    Regra 2: se o preço caiu desde a última vez, pode (é notícia nova).
    Regra 3: senão, só depois do intervalo mínimo.
    """
    anterior = ultima_aparicao(historico, oferta["id_anuncio"])
    if anterior is None:
        return True, "produto novo"

    preco_hoje = para_numero(oferta["preco_por"])
    preco_antes = para_numero(anterior["preco_por"])
    if preco_hoje < preco_antes:
        return True, f"preço caiu ({formatar_reais(preco_antes)} -> {formatar_reais(preco_hoje)})"

    dias = (hoje - date.fromisoformat(anterior["data"])).days
    if dias >= INTERVALO_DIAS:
        return True, f"última vez há {dias} dias"
    return False, f"saiu há {dias} dia(s); espera {INTERVALO_DIAS}"


def montar_texto(oferta):
    """Monta o texto do post no formato do grupo."""
    preco_de = para_numero(oferta["preco_de"])
    preco_por = para_numero(oferta["preco_por"])
    desconto = round((1 - preco_por / preco_de) * 100) if preco_de > preco_por else 0

    linhas = [f"🦷 *{oferta['titulo']}*", ""]
    if desconto > 0:
        linhas.append(f"~De {formatar_reais(preco_de)}~")
        linhas.append(f"🔥 *Por {formatar_reais(preco_por)}* ({desconto}% OFF)")
    else:
        linhas.append(f"🔥 *{formatar_reais(preco_por)}*")
    if oferta.get("por_que_vale"):
        linhas += ["", f"✅ {oferta['por_que_vale']}"]
    linhas += ["", f"👉 {oferta['link_afiliado']}"]
    return "\n".join(linhas), desconto


def pegar_imagem(oferta, destino):
    """
    Consegue a imagem do anúncio de um destes jeitos:
      - arquivo_imagem: caminho de uma imagem já salva -> só copia
      - url_imagem: endereço da imagem -> baixa
    Se não der, avisa e segue sem travar a rodada. Devolve True se conseguiu.
    """
    arquivo = (oferta.get("arquivo_imagem") or "").strip()
    if arquivo:
        origem = Path(arquivo)
        if not origem.is_absolute():
            origem = PASTA_PROJETO / origem
        if origem.exists():
            shutil.copyfile(origem, destino)
            return True
        print(f"   ⚠️  arquivo de imagem não encontrado: {origem}")
    return baixar_imagem(oferta.get("url_imagem", ""), destino)


def baixar_imagem(url, destino):
    """Baixa a imagem do anúncio. Se falhar, avisa e segue sem travar a rodada."""
    if not url:
        return False
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(pedido, timeout=20) as resposta:
            destino.write_bytes(resposta.read())
        return True
    except Exception as erro:
        print(f"   ⚠️  não consegui baixar a imagem: {erro}")
        return False


# ---------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------
def main():
    simular = "--simular" in sys.argv
    hoje = date.today()

    ofertas = ler_csv(ARQ_OFERTAS)
    historico = ler_csv(ARQ_HISTORICO)
    if not ofertas:
        print(f"Nenhuma oferta em {ARQ_OFERTAS}. Nada a fazer.")
        return

    # Quantas ofertas de cada categoria já saíram hoje (contando o histórico)
    por_categoria = {}
    for h in historico:
        if h["data"] == hoje.isoformat():
            por_categoria[h["categoria"]] = por_categoria.get(h["categoria"], 0) + 1

    # Cada rodada ganha sua própria pasta (data + hora), assim nada é sobrescrito
    rodada = datetime.now().strftime("%Hh%M")
    pasta_dia = PASTA_SAIDA / hoje.isoformat() / rodada
    pasta_painel = pasta_dia / "painel"
    pasta_painel.mkdir(parents=True, exist_ok=True)

    aprovadas, textos_finais = [], []
    print(f"Rodada de {hoje.strftime('%d/%m/%Y')} - {len(ofertas)} ofertas recebidas\n")

    for oferta in ofertas:
        if len(aprovadas) >= MAX_POSTS_POR_RODADA:
            print(f"Limite de {MAX_POSTS_POR_RODADA} posts atingido. Parando.")
            break

        titulo = oferta["titulo"]
        categoria = oferta.get("categoria", "outros")

        ok, motivo = pode_postar(oferta, historico, hoje)
        if not ok:
            print(f"⏭️  {titulo} -> pulada: {motivo}")
            continue
        if por_categoria.get(categoria, 0) >= MAX_POR_CATEGORIA:
            print(f"⏭️  {titulo} -> pulada: categoria '{categoria}' já tem {MAX_POR_CATEGORIA} hoje")
            continue

        numero = len(aprovadas) + 1
        texto, desconto = montar_texto(oferta)
        print(f"✅ {numero:02d}. {titulo} -> {motivo}")

        imagem = pasta_dia / f"{numero:02d}_{oferta['id_anuncio']}.jpg"
        tem_imagem = pegar_imagem(oferta, imagem)

        # Documento do Painel de Ofertas (um JSON por post)
        doc = {
            "doc_id": f"{hoje.isoformat()}_{rodada}_{numero:02d}",
            "data": hoje.isoformat(),
            "rodada": rodada,
            "ordem": numero,
            "id_anuncio": oferta["id_anuncio"],
            "titulo": titulo,
            "categoria": categoria,
            "preco_de": para_numero(oferta["preco_de"]),
            "preco_por": para_numero(oferta["preco_por"]),
            "desconto_pct": desconto,
            "link_afiliado": oferta["link_afiliado"],
            "texto": texto,
            "status": "sugerida",
            "exemplo": False,
            # caminho local da imagem; trocado pelo id do asset ao subir no painel
            "imagem_arquivo": str(imagem) if tem_imagem else None,
        }
        (pasta_painel / f"{numero:02d}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

        textos_finais.append(f"===== POST {numero:02d} =====\n{texto}\n")
        por_categoria[categoria] = por_categoria.get(categoria, 0) + 1
        aprovadas.append({
            "data": hoje.isoformat(),
            "id_anuncio": oferta["id_anuncio"],
            "titulo": titulo,
            "categoria": categoria,
            "preco_de": oferta["preco_de"],
            "preco_por": oferta["preco_por"],
            "desconto_pct": desconto,
            "link_afiliado": oferta["link_afiliado"],
            "status": "sugerida",
        })

    # Salva todos os textos num arquivo só, fácil de copiar para o WhatsApp
    (pasta_dia / "posts.txt").write_text("\n".join(textos_finais), encoding="utf-8")
    print(f"\n{len(aprovadas)} post(s) prontos em {pasta_dia}")
    print(f"Pacote do painel em {pasta_painel}")

    if simular:
        print("Modo simulação: histórico NÃO foi alterado.")
        return

    # Acrescenta as aprovadas no final do histórico
    novo_arquivo = not ARQ_HISTORICO.exists() or ARQ_HISTORICO.stat().st_size == 0
    with open(ARQ_HISTORICO, "a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_HISTORICO)
        if novo_arquivo:
            escritor.writeheader()
        escritor.writerows(aprovadas)
    print(f"Histórico atualizado: +{len(aprovadas)} linha(s).")


if __name__ == "__main__":
    main()
