# claude-memory-hooks

> O Claude Code lembra. Sem servidor, sem banco, sem chave de API, sem dependências.

[Read in English](README.md)

---

## Tr�s partes, uma instala��o

| | o que � | estado |
|---|---|---|
| **[`engine/`](engine/)** | a mem�ria: lembra entre sess�es e traz o que � relevante ao que voc� digitou | pronto |
| **[`method/`](method/)** | como o trabalho � feito � como travas que **recusam**, n�o como conselho | pronto |
| **[`knowledge/`](knowledge/)** | 56 li��es que sobrevivem ao projeto onde nasceram, como notas que o motor indexa | pronto |

D� para levar s� a primeira. As tr�s juntas s�o o ponto: mem�ria sem nada que
valha lembrar � arquivo vazio, e m�todo que ningu�m faz cumprir � desejo.

Instala��o: `bash install.sh` traz a mem�ria; `bash install.sh --full` traz
tamb�m o m�todo. O `--full` � opcional de prop�sito � as travas **recusam**
coisas, e isso deve ser decis�o, n�o surpresa. · [De onde vêm os números](docs/MEASUREMENTS.md)

---

## O problema

Quem usa o Claude Code de verdade bate nestas três paredes:

1. **Ele esquece tudo entre sessões** — você reexplica o mesmo contexto todo dia.
2. **Vários projetos, nenhuma continuidade** — trocar de projeto é recomeçar do zero.
3. **O trabalho some quando você não salva** — fechou a sessão, foi embora o porquê de cada decisão.

## O que isto faz

Quatro scripts que rodam calados dentro do Claude Code:

| Script | Quando roda | O que faz |
|---|---|---|
| `session_context.py` | ao abrir a sessão | Injeta o resumo da última sessão deste projeto |
| `prompt_memory.py` | quando você digita | Ranqueia todas as suas notas e injeta as relevantes |
| `auto_brief.py` | ao fechar a sessão | Escreve o resumo a partir da transcrição |
| `reindex_memory.py` | ao abrir e ao fechar | Mantém o índice de busca em dia |

A memória fica em Markdown puro, que você lê, edita, move ou apaga. Remover a
ferramenta não remove a memória.

**Nenhuma chamada a LLM. Nenhuma chave de API. Nada rodando em segundo plano.
Só a biblioteca padrão do Python.**

---

## Como é na prática

**Antes**

> Você: "Então, continuando de ontem, a gente estava no webhook de pagamento, onde o retry—"
> Claude: "Não tenho contexto de sessões anteriores..."

**Depois**

> *(a sessão abre)*
> O Claude já sabe: o projeto, a última tarefa, o próximo passo, o que está travado.
> Você só continua.

E no meio da conversa, quando você cita algo de semanas atrás em outro projeto, a
nota volta sozinha — você não precisou lembrar que ela existia.

---

## Instalação

**Requisitos:** Python 3.8+ e Claude Code. A lista acaba aqui.

```bash
git clone https://github.com/oliveirarenanfelipe/claude-memory-hooks
cd claude-memory-hooks
bash install.sh
```

Reinicie o Claude Code. Funciona na hora, sem configurar nada.

Para ajustar, rode `/memory-setup` — uma conversa curta que escreve a
configuração por você. Para remover tudo: `bash uninstall.sh` (as suas notas
ficam).

O instalador é idempotente: rodar de novo atualiza e nunca registra nada em
duplicata. Ele faz cópia de segurança do `settings.json` antes de tocar nele.

---

## Como funciona de verdade

Hooks do Claude Code podem devolver `hookSpecificOutput.additionalContext`.
**Qualquer texto colocado ali entra no contexto do modelo.** Esse é o mecanismo
inteiro — todo o resto deste repositório é sobre decidir *qual* texto.

Decidir bem é a parte difícil:

- **Busca ranqueada, não casamento de palavra.** BM25 sobre todas as notas de
  todos os projetos, com índice invertido: uma busca custa cerca de um
  milissegundo.
- **Ele sabe onde você está.** Nota do projeto aberto ganha da nota do vizinho —
  como multiplicador, nunca como filtro, para que a do vizinho ainda vença quando
  for genuinamente a resposta.
- **Nota longa é fatiada por título, não truncada.** O que está escrito no fim de
  uma nota de 20 mil caracteres continua alcançável.
- **O resultado é deduplicado por arquivo**, para um documento longo não ocupar
  as cinco vagas e expulsar as outras quatro respostas.
- **Resumo escrito à mão nunca é sobrescrito.** Marque `curated: true` e o
  automático sai de cena, deixando um rodapé datado avisando que houve trabalho
  depois.
- **Quando nenhuma memória é injetada, o log diz por quê.** "Demorou demais" e
  "não achou nada" pedem consertos opostos e não podem parecer a mesma coisa.

Cada número por trás dessas escolhas — o orçamento, os pesos, o tamanho da fatia
— foi medido num acervo real. Estão escritos em
[docs/MEASUREMENTS.md](docs/MEASUREMENTS.md), junto com o que foi testado e
reprovado.

---

## Configuração

Tudo é opcional. Copie `memory-hooks/config.example.json` para
`~/.claude/memory-hooks/config.json` e mantenha só o que você mudar.

```json
{
  "language": "pt",
  "project_roots": ["C:/Users/eu/Projetos"],
  "layers": [
    { "name": "manual", "path": "C:/Users/eu/Notas/manual",
      "mode": "flat", "scope": "global" }
  ]
}
```

- **`project_roots`** — onde ficam seus projetos. Só muda como o nome aparece:
  com isso, `app`; sem isso, `c-users-eu-projetos-app`. Os dois funcionam.
- **`layers`** — pastas de notas fora de `~/.claude/projects/`: um manual, um
  vault do Obsidian, uma pasta de padrões. `scope: "global"` faz a camada valer
  em todo projeto. Prefira a lista `folders` a `mode: "recursive"` — varredura
  recursiva numa pasta que ninguém curou traz para dentro o que estiver lá.
- **`weights`, `budget_ms`, `note_cap`** — os botões de ranking e desempenho.
  Leia [docs/MEASUREMENTS.md](docs/MEASUREMENTS.md) antes de mexer: cada padrão
  está segurando alguma coisa.

Configuração quebrada cai nos padrões em vez de derrubar a sua sessão.

---

## Testes, e um gate que consegue reprovar

```bash
python tests/test_memory.py             # 36 checagens nas guardas
python tests/golden_recall.py           # gate de ranking e desempenho
python tests/golden_recall.py --mutate  # quebra de propósito; o gate tem de reprovar
```

Sem pytest, sem dependências, e rodam contra um acervo sintético em
`tests/fixtures/` — nunca contra as suas notas.

O `golden_recall.py` diz *qual* nota tem de voltar e *em que posição*. Um teste
que só afirma "voltou alguma coisa" fica verde enquanto o ranking é destruído.

O `--mutate` é a parte que vale copiar para os seus projetos. Ele quebra de
propósito aquilo que cada caso protege — faz o vizinho ganhar do projeto aberto,
remove as camadas extras, desliga o fatiamento — e **falha se o gate não
perceber**. Gate que só passou não é prova; ele ficaria verde numa regressão de
verdade também.

O CI roda os três no Linux, macOS e Windows, em Python 3.8 e 3.12.

---

## Onde a sua memória mora

```
~/.claude/
  projects/<caminho-do-projeto-codificado>/memory/
      project_*.md              suas notas
      session_briefs/<slug>.md  o resumo automático
  memory-hooks/config.json      sua configuração
  hooks/recall.log              por que cada prompt recebeu a memória que recebeu
```

O índice (`projects/_index/`) é derivado. Apague quando quiser; a próxima sessão
reconstrói a partir do Markdown.

---

## Filosofia

Isto nasceu estudando o [claude-mem](https://github.com/thedotmack/claude-mem),
que roda um servidor local permanente, SQLite e ChromaDB para busca semântica. É
um trabalho poderoso.

Aqui o mesmo trabalho central é feito com scripts Python e arquivos Markdown.
Nada para manter rodando, nada para quebrar, nada para pagar, e nenhum serviço
que possa sumir levando a sua memória junto.

A troca é real e merece ser dita na cara: **busca léxica, não semântica.** Se
você perguntar por "autenticação" e a sua nota disser "login", o BM25 não liga as
duas — um banco vetorial ligaria. Em troca, você recebe resultados que consegue
explicar, um índice que reconstrói em segundos, zero infraestrutura, e notas que
continuam suas num formato que ainda vai abrir daqui a dez anos.

---

## Licença

MIT — faça o que quiser com isto.
