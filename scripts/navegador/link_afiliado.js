// Roda na PÁGINA DO PRODUTO (produto.mercadolivre.com.br/MLB-<numero>).
// 1. Confere preço atual e se o anúncio cita registro na Anvisa.
// 2. Clica em "Compartilhar" (barra de Afiliados) e lê o link meli.la gerado.
// 3. Fecha o painel de compartilhar.
// Devolve: { preco, anvisa, link } ou { erro }
await (async () => {
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const txt = document.body.innerText;
  const precoEl = document.querySelector(".ui-pdp-price__second-line .andes-money-amount, [data-testid='price-part'] .andes-money-amount");
  const parte = (el, s) => (el && el.querySelector(s) || {}).innerText || "";
  const preco = precoEl ? parseFloat(parte(precoEl, ".andes-money-amount__fraction").replace(/\./g, "") + "." + (parte(precoEl, ".andes-money-amount__cents") || "00")) : null;
  const anvisa = /anvisa/i.test(txt) ? 1 : 0;

  const botao = [...document.querySelectorAll("button, a")].find((b) => b.innerText.trim() === "Compartilhar" && b.getBoundingClientRect().top < 80);
  if (!botao) return JSON.stringify({ preco, anvisa, erro: "botão Compartilhar da barra de Afiliados não encontrado (está logado na conta de afiliado?)" });
  botao.click();

  let link = null;
  for (let i = 0; i < 20 && !link; i++) {
    await espera(300);
    link = [...document.querySelectorAll("input, textarea")].map((e) => e.value).find((v) => /^https:\/\/meli\.la\//.test(v)) || null;
  }
  document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  return JSON.stringify(link ? { preco, anvisa, link } : { preco, anvisa, erro: "link não apareceu em 6s" });
})()
