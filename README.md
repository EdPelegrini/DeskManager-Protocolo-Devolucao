# Protocolo de Devolução automático (Desk Manager + Maestro)

Gera a **etiqueta de protocolo de devolução** do carrinho a partir de um chamado do Desk Manager, com um clique, e imprime em uma Zebra ZD230.

> **Todos os dados deste repositório são fictícios** (empresa, prefixo do ambiente, chaves, códigos de grupo, operadores e chamados). Adapte os valores ao seu ambiente.

## O problema
O carrinho de devolução era identificado só pelo número do chamado. As informações (produto, quantidade, setor, câmara fria...) ficavam apenas no Desk.

## Como funciona

```
Área autoriza a devolução  ──>  ação "DEVOLUÇÃO DE PRODUTO" no chamado
Operador clica em "Imprimir protocolo de devolução"  (Ação Rápida, tipo 1)
   └─> Maestro (PARSE_Etiqueta.py)
         ├─ busca o chamado           POST /ChamadosSuporte/lista
         ├─ busca os campos extras    POST /ChamadosSuporte/camposextras
         ├─ busca as ações            POST /ChamadoHistoricos/lista
         └─ busca o grupo do operador POST /Operadores
   └─> devolve um modal com o HTML da etiqueta (5 etiquetas de 80x40 mm)
Operador clica em "Imprimir protocolo"  ──>  impressão local na ZD230
```

Sem a ação de autorização no chamado, a etiqueta sai com o aviso **"Devolução ainda não autorizada"**.

### O que sai na etiqueta
- **Da ação de autorização:** operador e grupo, data, quantidade, nome do produto, setor e câmara fria (lidos do texto da ação: `( ) Opção` / `(x) Opção`).
- **Do chamado:** número, cliente, assunto, criação, data da compra, GFP/boleta, tipo de compra e produtor.

## Estrutura

| Caminho | O que é |
|---|---|
| `src/PARSE_Etiqueta.py` | Bloco Python do Maestro (busca os dados e monta o HTML) |
| `tools/montar_fluxo.js` | Cria/atualiza o Maestro e publica o fluxo (`--criar`, `--publicar <chave>`) |
| `docs/maestro.config.exemplo.json` | Exemplo de "memória do projeto" (papel, blocos, gotchas, histórico) |
| `docs/regua_zd230.html` | Página de calibração (régua 80x40 mm) para testar a impressora |
| `docs/apresentacao.pptx` | Apresentação do projeto (com dados fictícios) |

## Como usar

**Pré-requisitos:** Node.js, um ambiente Desk Manager com o recurso Maestro e uma *Chave de API de integração* (a do operador não cria Maestro).

1. **Autenticar** (a resposta é o token; guarde em um arquivo que **não** vai para o git):
   ```bash
   # salve o corpo em um arquivo para evitar problemas de aspas no Windows
   echo '{"PublicKey":"SUA_CHAVE_DO_AMBIENTE"}' > corpo.json
   curl -s -X POST https://api.desk.ms/Login/autenticar \
     -H "Authorization: SUA_CHAVE_DE_INTEGRACAO" -H "Content-Type: application/json" \
     --data-binary @corpo.json > token.txt
   ```
2. **Criar o Maestro e publicar o fluxo:**
   ```bash
   export DESK_HOST=https://SEU_PREFIXO.desk.ms
   node tools/montar_fluxo.js token.txt --criar          # devolve a chave do Maestro
   node tools/montar_fluxo.js token.txt --publicar 12345 # use a chave devolvida
   ```
   O fluxo usa o cron `CRON_access_token` (o seu ambiente precisa de um cron de autenticação com esse nome).
3. **Criar a Ação Rápida** (`PUT /ARMaestro`, `Menu=ARMaestro&App=Panel`) apontando para a URL do Maestro:
   ```json
   {"TARMaestro": {"Chave": "", "Nome": "Imprimir protocolo de devolução",
     "URLMaestro": "<campo Token do Maestro>", "Tipo": "1",
     "JFiltros": "{\"Grupos\":[\"000101\",\"000102\"],\"Icon\":\"print\",\"Checkbox\":\"All\"}"}}
   ```
   O botão aparece em **Ação Avançada > Interagir no Chamado > Ações Rápidas Maestro**.

## Impressão (Zebra ZD230)
Padrão testado, igual em todas as máquinas:
- Driver **ZDesigner ZD230-203dpi ZPL**, papel **80 x 40 mm**, **etiquetas contínuas**.
- Janela de impressão do navegador: **Escala 100%** e **Margens: Nenhuma**.
- Um driver de **300 dpi** imprime a mesma etiqueta ~1,4x maior e cortada.

O tamanho do texto, margens e o espaço para a fita ficam em `d_layout`, no topo de `src/PARSE_Etiqueta.py`.

## Pontos de atenção
- Quantidade, produto, setor e câmara fria saem de **texto livre** da ação. Se o modelo do texto mudar, a etiqueta pode sair em branco (melhoria sugerida: campos estruturados na ação).
- O filtro de **grupos** da Ação Rápida vale para o **grupo do chamado**, não do operador.
- A página do protocolo é um HTML temporário servido pelo Maestro; o computador do operador precisa de internet.
- Os trechos "Dentro/Fora da empresa" removidos do assunto (`l_ignorar`) são específicos do ambiente: ajuste.

## Segurança
Nunca coloque chaves de API, tokens ou a URL do Maestro (`?token=`) no repositório. O `.gitignore` já ignora arquivos de token e `.env`.
