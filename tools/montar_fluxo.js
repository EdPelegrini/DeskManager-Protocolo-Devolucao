// Monta e (com --criar / --publicar) grava o Maestro "Protocolo de Devolucao - Etiqueta" no seu ambiente Desk Manager.
// Uso: node montar_fluxo.js <arquivo_token> [--criar | --publicar <chave>]
const fs = require("fs");
const path = require("path");

const HOST = process.env.DESK_HOST || "https://SEU_PREFIXO.desk.ms"; // ex.: https://meuprefixo.desk.ms
const token = fs.readFileSync(process.argv[2], "utf8").replace(/"/g, "").trim();
const modo = process.argv[3] || "dry";
const chave = process.argv[4] || "";

const py = fs.readFileSync(path.join(__dirname, "..", "src", "PARSE_Etiqueta.py"), "utf8");

const initModel = {
  codmodal: "", cod_chamado: "", codchamado: "", chamado_cod: "",
  chave_chamado: "", chamado: "", operador_cod: "", grupo_cod: "", idioma: ""
};

const fluxo = {
  config: [
    { name: "BEGIN_init", response_model: JSON.stringify(initModel) },
    { name: "PARSE_Etiqueta", jsonata: py, response_model: JSON.stringify({ modal: "" }) }
  ],
  tree: "BEGIN_init;BEGIN_init.PARSE_Etiqueta;",
  constants: [],
  cron: ["CRON_access_token"]
};

// checagens do pre-voo (o validador oficial e em Python, que nao existe nesta maquina)
const nomes = fluxo.config.map(b => b.name);
const noTree = fluxo.tree.split(";").filter(Boolean).map(e => e.split(".").pop());
for (const n of noTree) if (!nomes.includes(n)) throw new Error("tree referencia bloco inexistente: " + n);
if (new Set(nomes).size !== nomes.length) throw new Error("nome de bloco duplicado");
for (const b of fluxo.config) for (const [k, v] of Object.entries(b)) if (k !== "name" && typeof v !== "string") throw new Error(b.name + "." + k + " nao e string");
console.log("pre-voo ok:", nomes.join(", "));

const descricao = "Autor: Seu Nome\n" +
  "O que faz: Acao Rapida no chamado que gera o protocolo de devolucao (etiqueta 80 mm) a partir do chamado, campos extras e acao DEVOLUCAO DE PRODUTO. Imprime 'Devolucao ainda nao autorizada' se a acao nao existir.\n" +
  "Cases: nenhum (fluxo linear: BEGIN_init -> PARSE_Etiqueta)\n\n" +
  "RECURSOS CRIADOS NESTE AMBIENTE:\n- (nenhum recurso de apoio alem deste Maestro; usa o cron CRON_access_token ja existente)";

// encoding minimo: escapa % e + (chr(37) por seguranca) e depois Base64
const pc = String.fromCharCode(37);
function codificarFluxo(obj) {
  const j = JSON.stringify(obj);
  const esc = j.split(pc).join(pc + "25").split("+").join(pc + "2B");
  return Buffer.from(esc, "utf8").toString("base64");
}

async function put(dados, extra) {
  const body = new URLSearchParams({ Dados: JSON.stringify(dados), ...extra });
  const r = await fetch(HOST + "/Maestro", {
    method: "PUT",
    headers: { Authorization: token, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
    body
  });
  return { status: r.status, texto: await r.text() };
}

(async () => {
  console.log("tamanho do fluxo (JSON):", JSON.stringify(fluxo).length, "bytes");
  if (modo === "--criar") {
    const r = await put({
      TMaestro: { Chave: "", UrlIcone: "", Fluxo: "", Modal: "S", ChaveBackup: "", Nome: "Protocolo de Devolucao - Etiqueta", Descricao: descricao, PermPerf: [""] },
      TMaestroConstante: []
    }, { Menu: "Maestro", App: "Panel" });
    console.log("criar:", r.status, r.texto);
  } else if (modo === "--publicar") {
    const r = await put({
      TMaestro: { Chave: chave, Fluxo: codificarFluxo(fluxo), Panel: "FluxoMConstrutor" }
    }, { Menu: "FluxoMConstrutor", App: "Ticket" });
    console.log("publicar:", r.status, r.texto);
  } else {
    console.log("dry run: nada gravado");
  }
})();
