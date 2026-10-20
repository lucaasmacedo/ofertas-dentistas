// Roda na PÁGINA DE BUSCA do Mercado Livre (lista.mercadolivre.com.br/...).
// Antes deste código, o Claude coloca uma linha com os critérios do termo:
//   const P = { desconto_min: 15, preco_min: 30, preco_max: 300,
//               chaves: { produto: "seringa", medidas: ["1ml"] } };
// (é só copiar os campos do termo em dados/rodada/termos.json)
// Devolve os 4 melhores anúncios num formato compacto (a ferramenta do
// navegador corta respostas longas):
//   [id, titulo, preco_de, preco_por, desconto_pct, so_pix, vendidos, full, frete_gratis, imagem]
// "imagem" é só o miolo do nome do arquivo; o endereço completo é
//   https://http2.mlstatic.com/D_Q_NP_2X_<imagem>-E.webp
(() => {
  const num = (el) => {
    if (!el) return null;
    const f = (el.querySelector(".andes-money-amount__fraction") || {}).innerText || "";
    const c = (el.querySelector(".andes-money-amount__cents") || {}).innerText || "00";
    return parseFloat(f.replace(/\./g, "") + "." + c);
  };
  const idDe = (s) => (s.match(/MLB-?\d{6,}/i) || [""])[0].replace("-", "").toUpperCase();
  const vistos = new Set();
  const cards = [...document.querySelectorAll(".poly-card")];
  const itens = cards.map((c) => {
    const a = c.querySelector("a.poly-component__title") || c.querySelector("a");
    if (!a) return null;
    const txt = c.innerText.replace(/\s+/g, " ");
    const de = num(c.querySelector("s.andes-money-amount--previous"));
    const por = num(c.querySelector(".poly-price__current"));
    const id = idDe(a.href) || idDe(c.innerHTML);
    const img = (c.querySelector("img.poly-component__picture") || c.querySelector("img") || {}).src || "";
    const miolo = (img.match(/D_\w+?_2X_(.+?)-[A-Z]\.\w+$/) || img.match(/D_\w+?_(.+?)-[A-Z]\.\w+$/) || [])[1] || "";
    const vend = (txt.match(/\+?\s?([\d.]+)( mil)? vendidos/) || []);
    const vendidos = vend[1] ? parseFloat(vend[1].replace(/\./g, "")) * (vend[2] ? 1000 : 1) : 0;
    return {
      id, titulo: a.innerText.trim().slice(0, 90), de: de || por, por,
      desc: de && por && de > por ? Math.round((1 - por / de) * 100) : 0,
      pix: /% OFF no Pix/i.test(txt) ? 1 : 0, vendidos,
      full: /FULL/.test(txt) ? 1 : 0, frete: /Frete gr[aá]tis|Chegará grátis|Chegar[aá] gr[aá]tis/i.test(txt) ? 1 : 0,
      miolo,
    };
  }).filter((x) => x && x.id && x.por && !vistos.has(x.id) && vistos.add(x.id));

  // Relevância: o título precisa ter o produto e pelo menos uma das medidas.
  // Normaliza: sem acentos, minúsculas, "1 ml" -> "1ml", "01ml" -> "1ml", "4,5" -> "4.5"
  const norm = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/(\d),(\d)/g, "$1.$2").replace(/(\d)\s+(ml|mm|g|cm|un|l)\b/g, "$1$2").replace(/\b0+(\d)/g, "$1");
  const relevante = (t) => {
    const n = norm(t), k = P.chaves || { produto: "", medidas: [] };
    const prod = norm(k.produto || "").replace(/s$/, "");
    if (prod && !n.includes(prod)) return false;
    // a medida precisa estar "sozinha": "1ml" casa com "1ml", mas não com "21ml"
    const tem = (m) => new RegExp("(^|[^0-9.])" + norm(m).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "(?![0-9])").test(n);
    return !k.medidas.length || k.medidas.some(tem);
  };
  const ok = itens.filter((x) => x.desc >= P.desconto_min && x.por >= P.preco_min && x.por <= P.preco_max && x.miolo && relevante(x.titulo));
  // Nota: desconto pesa mais; vendidos e envio Full/grátis desempatam
  const nota = (x) => x.desc + Math.min(15, Math.log10(1 + x.vendidos) * 4) + x.full * 3 + x.frete * 2;
  ok.sort((a, b) => nota(b) - nota(a));
  const top = ok.slice(0, 4).map((x) => [x.id, x.titulo, x.de, x.por, x.desc, x.pix, x.vendidos, x.full, x.frete, x.miolo]);
  return JSON.stringify({ anuncios: itens.length, aprovados: ok.length, top });
})()
