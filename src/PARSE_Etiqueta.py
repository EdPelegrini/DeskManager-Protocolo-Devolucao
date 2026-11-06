#python,d_modal!

global f_api, f_texto, f_esc, f_cod_chamado, f_data_hora, f_assunto, f_extra, f_marcados, f_quantidade_acao, f_produto_acao, f_pagina, f_lab, f_etiqueta, f_montar, d_layout

import maestroutils
import json
import base64

# padrao de impressao dos portais (ZD230 203 dpi, driver continuo 80x40, escala 100%): tamanho REAL em mm / pt
# topo = espaco livre para a fita na etiqueta do topo da tira; base = margem superior de cada etiqueta
d_layout = {"esq": 5, "largura": 68, "fonte": 11.5, "titulo": 10.8, "topo": 12, "base": 3}

d_init = memoria["BEGIN_init"]

#=================================================
# Chamada a API Desk Manager com o token do cron de integracao
def f_api(s_path, d_body):
  import maestroutils
  import json

  try:
    d_ret = maestroutils.apiDeskManager(
      spath=s_path,
      sbody=json.dumps(d_body),
      sauth=memoria["CRON_access_token"]["access_token"]
    )
  except Exception as o_erro:
    raise Exception(s_path + ": " + str(o_erro))

  return d_ret.get("responsejson", {})

#=================================================
# HTML da Descricao da acao -> texto simples
def f_texto(s_html):
  import re

  s_txt = re.sub(r"<[^>]+>", " ", s_html or "")
  s_txt = s_txt.replace("&nbsp;", " ").replace("&amp;", "&").replace("\xa0", " ")

  return re.sub(r"\s+", " ", s_txt).strip()

#=================================================
# Escapa texto que vai para dentro do HTML
def f_esc(s_valor):
  s_txt = str(s_valor if s_valor is not None else "")

  return s_txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

#=================================================
# Codigo do chamado (formato 0000-000000) vindo da Acao Rapida
def f_cod_chamado(d_entrada):
  l_campos = ["codmodal", "cod_chamado", "codchamado", "chamado_cod", "chave_chamado", "chamado"]

  for s_campo in l_campos:
    v_valor = d_entrada.get(s_campo, "")
    if isinstance(v_valor, str) and v_valor.strip() != "":
      return v_valor.strip()

  return ""

#=================================================
# 2026-10-01 + 08:13:50 -> 01/10/2026 - 08:13:50
def f_data_hora(s_data, s_hora):
  l_partes = str(s_data or "").split("-")

  if len(l_partes) == 3 and len(l_partes[0]) == 4:
    s_data = l_partes[2] + "/" + l_partes[1] + "/" + l_partes[0]

  return (s_data + " - " + str(s_hora or "")).strip(" -")

#=================================================
# Assunto sem os trechos genericos (categoria raiz e local Dentro/Fora da empresa) - AJUSTE para o seu ambiente
def f_assunto(s_assunto):
  l_ignorar = ["central de atendimento", "dentro da empresa", "fora da empresa"]
  l_saida = []

  for s_parte in str(s_assunto or "").split(" - "):
    if s_parte.strip().lower() not in l_ignorar:
      l_saida.append(s_parte.strip())

  return " - ".join(l_saida)

#=================================================
# Valor de um campo extra pelo nome (exato, sem diferenciar maiuscula)
def f_extra(l_extras, s_nome, b_contem):
  for d_campo in l_extras:
    s_atual = str(d_campo.get("nomecampoextra", "")).strip().lower()
    if (b_contem and s_nome in s_atual) or ((not b_contem) and s_atual == s_nome):
      return str(d_campo.get("valcampoextra", "")).strip()

  return ""

#=================================================
# Opcoes "( ) Nome" / "(x) Nome" da descricao -> [[nome, marcado]]
def f_marcados(s_texto):
  import re

  l_saida = []

  for o_achado in re.finditer(r"\(\s*([xX]?)\s*\)\s*([A-Za-zÀ-ÿ]+)", s_texto):
    l_saida.append([o_achado.group(2), o_achado.group(1) != ""])

  return l_saida

#=================================================
# Quantidade informada na acao de devolucao ("Quantidade: 6 cestos"), ate o "Setor:"
def f_quantidade_acao(s_texto):
  import re

  o_achado = re.search(r"Quantidade\s*:\s*(.*?)\s*(?:Setor\s*:|\(\s*[xX]?\s*\)|$)", s_texto, re.IGNORECASE)

  if o_achado:
    return o_achado.group(1).strip()

  return ""

#=================================================
# Nome do produto informado na acao de devolucao ("NOME DO PRODUTO: ..."), ate "Quantidade:"
def f_produto_acao(s_texto):
  import re

  o_achado = re.search(r"NOME\s+DO\s+PRODUTO\s*:\s*(.*?)\s*(?:Quantidade\s*:|Setor\s*:|\(\s*[xX]?\s*\)|$)", s_texto, re.IGNORECASE)

  if o_achado:
    return o_achado.group(1).strip()

  return ""

#=================================================
# Estrutura e estilo da pagina de impressao (80 mm)
def f_pagina(s_etiquetas):
  # cada etiqueta e uma pagina de 80x40 mm (mesmo tamanho do driver da ZD230); largura, margem e fonte vem de d_layout
  s_larg = str(d_layout["largura"]) + "mm"
  s_esq = str(d_layout["esq"]) + "mm"
  s_fonte = str(d_layout["fonte"]) + "pt"
  s_tit = str(d_layout["titulo"]) + "pt"
  s_base = str(d_layout["base"]) + "mm"

  s_css = "@page{size:80mm 40mm;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;color:#000}"
  s_css += ".lab{width:80mm;height:40mm;overflow:hidden;padding:" + s_base + " 0 0 " + s_esq + ";page-break-after:always;break-after:page;border-bottom:1px dotted #bbb}"
  s_css += ".lab:last-child{page-break-after:auto;break-after:auto}"
  s_css += ".in{width:" + s_larg + ";font-size:" + s_fonte + ";line-height:1.2;text-transform:uppercase}"
  s_css += ".o{white-space:nowrap;margin-right:3mm}.t{text-align:center;font-weight:700;font-size:" + s_tit + "}.sep{border-top:1px dashed #000;margin:.4mm 0 1mm}"
  s_css += "p{margin:0;word-break:break-word}.aviso{border:2px solid #000;padding:3mm;text-align:center;font-weight:800;margin-top:3mm}"
  s_css += ".bar{text-align:center;padding:8px;background:#f1f1f1;font-size:13px}.bar button{padding:6px 18px;font-size:14px;cursor:pointer}"
  s_css += ".wrap{display:flex;flex-direction:column-reverse;align-items:flex-start}"
  s_css += "@media print{.bar{display:none}.lab{border-bottom:0}.wrap{display:block}}"

  s_html = "<!DOCTYPE html><html lang=\"pt-br\"><head><meta charset=\"utf-8\"><title>Protocolo de Devolução</title><style>" + s_css + "</style></head><body>"
  s_html += "<div class=\"bar\"><button onclick=\"window.print()\">Imprimir protocolo</button></div>"
  s_html += "<div class=\"wrap\">" + s_etiquetas + "</div></body></html>"

  return s_html

#=================================================
# Uma etiqueta 80x40: titulo centralizado com a paginacao + corpo
def f_lab(s_titulo, s_corpo, n_topo=0):
  s_cab = ""
  if s_titulo != "":
    s_cab = "<p class=\"t\">" + s_titulo + "</p><div class=\"sep\"></div>"

  # n_topo = espaco livre extra (mm) acima do conteudo, para a fita de colar no carrinho
  s_estilo = ""
  if n_topo > 0:
    s_estilo = " style=\"padding-top:" + str(d_layout["base"] + n_topo) + "mm\""

  return "<div class=\"lab\"" + s_estilo + "><div class=\"in\">" + s_cab + s_corpo + "</div></div>"

#=================================================
# Corpo da etiqueta com os dados ja coletados
def f_etiqueta(d_dados):
  s_chamado = "<p>Chamado: " + f_esc(d_dados["cod"]) + "</p>"

  if not d_dados["autorizado"]:
    return f_lab("Devolução de produto", s_chamado + "<div class=\"aviso\">Devolução ainda<br>não autorizada</div>", d_layout["topo"])

  # etiqueta 1: identificacao (titulo e chamado so aqui); com o espaco livre no topo para a fita
  s_um = s_chamado
  s_um += "<p>Cliente: " + f_esc(d_dados["cliente"]) + "</p>"

  # etiqueta 2: autorizacao + quantidade
  s_aut = "<p class=\"t\">Autorização da devolução</p><div class=\"sep\"></div>"
  s_aut += "<p>Criação: " + f_esc(d_dados["acao_data"]) + "</p>"
  s_aut += "<p>Operador: " + f_esc(d_dados["operador"]) + "</p>"
  s_aut += "<p>Quantidade: " + f_esc(d_dados["quantidade"]) + "</p>"

  # etiqueta 3: setor e camara fria
  s_dois = ""

  l_setor = d_dados["setor"]
  l_camara = d_dados["camara"]

  if len(l_setor) == 0 and len(l_camara) == 0:
    s_dois += "<p>" + f_esc(d_dados["acao_texto"]) + "</p>"
  else:
    s_dois += "<p>Setor:</p>"
    s_linha = ""
    i_pos = 0
    for l_item in l_setor:
      s_marca = "(X)" if l_item[1] else "( )"
      s_linha += "<span class=\"o\">" + s_marca + "&nbsp;" + f_esc(l_item[0]) + "</span> "
      i_pos += 1
      if i_pos % 2 == 0:
        s_dois += "<p>" + s_linha + "</p>"
        s_linha = ""
    if s_linha != "":
      s_dois += "<p>" + s_linha + "</p>"

    s_camara_linha = "Câmara fria: "
    for l_item in l_camara:
      s_marca = "(X)" if l_item[1] else "( )"
      s_camara_linha += "<span class=\"o\">" + s_marca + "&nbsp;" + f_esc(l_item[0]) + "</span> "
    s_dois += "<p>" + s_camara_linha + "</p>"

  # etiqueta 4: secao "Dados chamado" (assunto, criacao, data da compra)
  s_dados1 = "<p class=\"t\">Dados chamado</p><div class=\"sep\"></div>"
  s_dados1 += "<p>Assunto: " + f_esc(d_dados["assunto"]) + "</p>"
  s_dados1 += "<p>Criação: " + f_esc(d_dados["criacao"]) + "</p>"
  s_dados1 += "<p>Data da compra: " + f_esc(d_dados["data_compra"]) + "</p>"

  # etiqueta 5: GFP, tipo de compra, produto e produtor
  s_dados2 = "<p>GFP / boleta: " + f_esc(d_dados["gfp"]) + "</p>"
  s_dados2 += "<p>Tipo de compra: " + f_esc(d_dados["tipo_compra"]) + "</p>"
  s_dados2 += "<p>Produto: " + f_esc(d_dados["produto"]) + "</p>"
  s_dados2 += "<p>Produtor: " + f_esc(d_dados["produtor"]) + "</p>"

  # impressao em ordem inversa (5a primeiro): a tira sai da impressora com a 1a etiqueta na ponta, entao a 1a fica no topo ao ler
  return f_lab("", s_dados2) + f_lab("", s_dados1) + f_lab("", s_dois) + f_lab("", s_aut) + f_lab("Devolução de produto", s_um, d_layout["topo"])

#=================================================
# Coleta os dados do chamado e devolve o corpo da etiqueta
def f_montar(s_cod):
  d_dados = {"cod": s_cod, "autorizado": False}

  d_lista = f_api("ChamadosSuporte/lista", {"Pesquisa": s_cod, "Ativo": "Todos", "Limit": "50"})
  d_chamado = {}
  for d_item in d_lista.get("root", []):
    if d_item.get("CodChamado") == s_cod:
      d_chamado = d_item

  if d_chamado == {}:
    return f_lab("Chamado não encontrado", "<p>" + f_esc(s_cod) + "</p>")

  s_chave = str(d_chamado["Chave"])

  d_extras = f_api("ChamadosSuporte/camposextras", {"Chave": s_chave})
  l_extras = d_extras.get("TCamposExtras", [])

  d_acoes = f_api("ChamadoHistoricos/lista",{"Chave": s_chave, "Solicitante": "N"})

  # acao de autorizacao = a mais recente cuja descricao contem "DEVOLUCAO DE PRODUTO"
  d_acao = {}
  s_ref = ""
  for d_item in d_acoes.get("root", []):
    s_txt = f_texto(d_item.get("Descricao", "")).upper().replace("Ç", "C").replace("Ã", "A")
    if "DEVOLUCAO DE PRODUTO" in s_txt:
      s_quando = str(d_item.get("DataCriacao", "")) + " " + str(d_item.get("HoraCriacao", ""))
      if s_quando > s_ref:
        s_ref = s_quando
        d_acao = d_item

  if d_acao == {}:
    return f_etiqueta(d_dados)

  d_dados["autorizado"] = True
  d_dados["cliente"] = f_extra(l_extras, "chave", False)
  d_dados["quantidade"] = f_extra(l_extras, "quantidade reclamada", True)
  d_dados["assunto"] = f_assunto(d_chamado.get("Assunto", ""))
  d_dados["criacao"] = f_data_hora(d_chamado.get("DataCriacao", ""), d_chamado.get("HoraCriacao", ""))
  d_dados["data_compra"] = f_extra(l_extras, "data da compra", False).replace("-", "/")
  d_dados["gfp"] = f_extra(l_extras, "gfp", True)
  d_dados["tipo_compra"] = f_extra(l_extras, "tipo de compra", True)
  d_dados["produto"] = f_extra(l_extras, "produto comprado", False)
  d_dados["produtor"] = f_extra(l_extras, "produtor", False)
  d_dados["acao_data"] = f_data_hora(d_acao.get("DataCriacao", ""), d_acao.get("HoraCriacao", ""))

  # operador da autorizacao + grupo principal do cadastro dele
  s_operador = ""
  s_grupo = ""
  l_operador = d_acao.get("Operador", [])
  if len(l_operador) > 0:
    s_operador = str(l_operador[0].get("text", ""))
    d_cad = f_api("Operadores", {"Chave": str(l_operador[0].get("id", ""))})
    l_grupo = d_cad.get("TOperador", {}).get("GrupoPrincipal", [])
    if isinstance(l_grupo, list) and len(l_grupo) > 0:
      s_grupo = str(l_grupo[0].get("text", ""))
  d_dados["operador"] = s_operador + (" | " + s_grupo if s_grupo != "" else "")

  # setor e camara fria: opcoes "( ) / (x)" da descricao da acao
  s_acao_texto = f_texto(d_acao.get("Descricao", ""))
  d_dados["acao_texto"] = s_acao_texto

  # a quantidade do protocolo e a da acao de devolucao; so cai na da abertura se a acao nao trouxer
  s_qtd_acao = f_quantidade_acao(s_acao_texto)
  if s_qtd_acao != "":
    d_dados["quantidade"] = s_qtd_acao

  # idem para o nome do produto: vale o que o operador escreveu na acao de devolucao
  s_prod_acao = f_produto_acao(s_acao_texto)
  if s_prod_acao != "":
    d_dados["produto"] = s_prod_acao

  d_dados["setor"] = []
  d_dados["camara"] = []
  for l_item in f_marcados(s_acao_texto):
    if l_item[0].lower() in ["sim", "não", "nao"]:
      d_dados["camara"].append(l_item)
    else:
      d_dados["setor"].append(l_item)

  return f_etiqueta(d_dados)

#=================================================
# EXECUCAO PRINCIPAL

s_cod = f_cod_chamado(d_init)

try:
  if s_cod == "":
    s_corpo = f_lab("Chamado não identificado", "<p>A ação não enviou o código do chamado.</p>")
  else:
    s_corpo = f_montar(s_cod)
except Exception as o_erro:
  s_corpo = f_lab("Erro ao gerar", "<p>" + f_esc(str(o_erro)) + "</p>")

s_b64 = base64.b64encode(f_pagina(s_corpo).encode("utf-8")).decode("utf-8")
s_url = maestroutils.base64toURLForceExt(s_b64, "html", "html")

d_modal = {
  "modal": {
    "title": "Protocolo de devolução",
    "button": "",
    "btnback": "",
    "iframe": {"url": s_url}
  }
}
