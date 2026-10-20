// Roda na PÁGINA DO PRODUTO (produto.mercadolivre.com.br/MLB-<numero>).
// 1. Confere preço atual e se o anúncio cita registro na Anvisa.
// 2. Clica em "Compartilhar" (barra de Afiliados) e lê o link meli.la gerado.
// 3. Fecha o painel de compartilhar.
// Devolve: { titulo, preco, anvisa, link } ou { titulo, erro }
// "titulo" é o da página, para conferir se abriu o produto certo.
await (async () => {
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const titulo = ((document.querySelector("h1") || {}).innerText || document.title).trim().slice(0, 80);
  const txt = document.body.innerText;
  const precoEl = document.querySelector(".ui-pdp-price__second-line .andes-money-amount, [data-testid='price-part'] .andes-money-amount");
  const parte = (el, s) => (el && el.querySelector(s) || {}).innerText || "";
  const preco = precoEl ? parseFloat(parte(precoEl, ".andes-money-amount__fraction").replace(/\./g, "") + "." + (parte(precoEl, ".andes-money-amount__cents") || "00")) : null;
  // textContent inclui partes escondidas (ex.: ficha técnica recolhida)
  const anvisa = /anvisa/i.test(document.body.textContent) ? 1 : 0;

  // A barra de Afiliados carrega depois da página: espera o botão até 6s
  const acharBotao = () => [...document.querySelectorAll("button, a")].find((b) => b.innerText.trim() === "Compartilhar" && b.getBoundingClientRect().top < 80);
  let botao = acharBotao();
  for (let i = 0; i < 20 && !botao; i++) { await espera(300); botao = acharBotao(); }
  if (!botao) return JSON.stringify({ titulo, preco, anvisa, erro: "botão Compartilhar da barra de Afiliados não encontrado (está logado na conta de afiliado?)" });
  // Às vezes a página ainda está carregando e o primeiro clique não abre o painel:
  // tenta até 3 vezes, esperando até 5s em cada.
  const lerLink = () => [...document.querySelectorAll("input, textarea")].map((e) => e.value).find((v) => /^https:\/\/meli\.la\//.test(v)) || null;
  let link = null;
  for (let tentativa = 0; tentativa < 3 && !link; tentativa++) {
    botao.click();
    for (let i = 0; i < 17 && !link; i++) {
      await espera(300);
      link = lerLink();
    }
  }
  document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  return JSON.stringify(link ? { titulo, preco, anvisa, link } : { titulo, preco, anvisa, erro: "link não apareceu após 3 tentativas" });
})()
