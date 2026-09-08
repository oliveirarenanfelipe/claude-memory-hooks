# claude-memory-hooks

> O Claude Code lembra, e trabalha do jeito que você decidiu.
> Sem servidor, sem banco, sem chave de API, sem dependências.

[![tests](https://github.com/oliveirarenanfelipe/claude-memory-hooks/actions/workflows/test.yml/badge.svg)](https://github.com/oliveirarenanfelipe/claude-memory-hooks/actions/workflows/test.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#)

[Read in English](README.md)

---

## Três partes, uma instalação

| | o que é | estado |
|---|---|---|
| **[`engine/`](engine/)** | a memória: lembra entre sessões e traz o que é relevante ao que você digitou | pronto |
| **[`method/`](method/)** | como o trabalho é feito — como travas que **recusam**, não como conselho | pronto |
| **[`knowledge/`](knowledge/)** | 56 lições que sobrevivem ao projeto onde nasceram, como notas que o motor indexa | pronto |

Dá para levar só a primeira. As três juntas são o ponto: memória sem nada que
valha lembrar é arquivo vazio, e método que ninguém faz cumprir é desejo.

---

## O problema

Quem usa o Claude Code de verdade bate nestas quatro paredes:

1. **Ele esquece tudo entre sessões** — você reexplica o mesmo contexto todo dia.
2. **Vários projetos, nenhuma continuidade** — trocar de projeto é recomeçar do zero.
3. **O trabalho some quando você não salva** — fechou a sessão, foi embora o porquê de cada decisão.
4. **As regras que você escreveu são ignoradas** — inclusive por você, com o documento carregado.

As três primeiras são o `engine/`. A quarta é a interessante, e é o `method/`.

---

## Instalação

**Requisitos:** Python 3.8+ e Claude Code. A lista acaba aqui.

```bash
git clone https://github.com/oliveirarenanfelipe/claude-memory-hooks
cd claude-memory-hooks

bash install.sh           # a memória
bash install.sh --full    # a memória mais o método
```

Reinicie o Claude Code. Funciona na hora, sem configurar nada.

O `--full` é opcional de propósito: as travas **recusam** coisas. Isso deve ser
decisão, não surpresa.

Para ajustar, rode `/memory-setup`. Para remover tudo, `bash uninstall.sh` — as
suas notas ficam nos dois casos. O instalador é idempotente e faz cópia de
segurança do `settings.json` antes de tocar nele.

---

## Como a memória funciona

Hooks do Claude Code podem devolver `hookSpecificOutput.additionalContext`.
**Qualquer texto colocado ali entra no contexto do modelo.** Esse é o mecanismo
inteiro — o resto é decidir *qual* texto.

- **Busca ranqueada, não casamento de palavra.** BM25 sobre todas as notas de
  todos os projetos, com índice invertido: uma busca custa cerca de um
  milissegundo.
- **Ele sabe onde você está.** Nota do projeto aberto ganha da do vizinho — como
  multiplicador, nunca como filtro, para que a do vizinho ainda vença quando for
  genuinamente a resposta.
- **Nota longa é fatiada por título, não truncada.** O que está no fim de uma
  nota de 20 mil caracteres continua alcançável.
- **O resultado é deduplicado por arquivo**, para um documento longo não ocupar
  as cinco vagas e expulsar as outras quatro respostas.
- **Resumo escrito à mão nunca é sobrescrito.** Marque `curated: true` e o
  automático sai de cena, deixando um rodapé datado avisando que houve trabalho
  depois.
- **Quando nenhuma memória é injetada, o log diz por quê.** "Demorou demais" e
  "não achou nada" pedem consertos opostos e não podem parecer a mesma coisa.

Cada número por trás dessas escolhas foi medido. Estão em
[`engine/docs/MEASUREMENTS.md`](engine/docs/MEASUREMENTS.md), junto com o que foi
testado e reprovado.

---

## Por que o método é código

Toda regra em `method/` existiu primeiro como frase num documento, e todas foram
violadas assim mesmo — por quem as escreveu, com o documento carregado.

O caso mais claro: uma nota escrita dezenove dias antes dizia, nestas palavras,
*"nunca por heredoc do shell"*. Estava indexada e alcançável. O erro aconteceu
assim mesmo e apagou cinco scripts e cinco registros de hook.

Daí a regra estreita: **prática que importa é trava, ou é desejo.**

São cinco: recusar arquivo novo sem quem o chame; recusar comando de shell
destrutivo; recusar escrita no projeto de outro; recusar edição que incha o
arquivo de instruções sempre carregado; e guardar a pasta de memória no git
sozinho, recusando guardar segredo.

Detalhe em [`method/README.md`](method/README.md).

---

## As 56 lições

Notas que voltam **sozinhas** quando o assunto encosta, em qualquer projeto. Não
é um documento que alguém precisa lembrar de abrir — é o oposto disso.

Começa por
[`the-check-that-passes-for-the-wrong-reason.md`](knowledge/the-check-that-passes-for-the-wrong-reason.md),
que é a lição sobre a qual o resto do repositório foi construído.

**Limitação declarada:** os casos das notas são reconstruídos. As lições vêm de
incidentes reais; as histórias que as ilustram foram reescritas com equivalentes
inventados, porque as originais contêm detalhe operacional de terceiros. Então os
**números ali são ilustrativos, não medidos**, e cada nota diz isso.

Detalhe em [`knowledge/README.md`](knowledge/README.md).

---

## Testes, e checagens que conseguem reprovar

```bash
make                                           # tudo
python engine/tests/test_memory.py             # 36 checagens nas guardas da memória
python engine/tests/golden_recall.py           # gate de ranking e desempenho
python engine/tests/golden_recall.py --mutate  # quebra de propósito
python method/gates/tests/test_gates.py        # 25 checagens nas travas + mutação
```

Sem pytest, sem dependências, e rodam contra acervos sintéticos — nunca contra as
suas notas.

O `--mutate` é a parte que vale copiar para os seus projetos. Ele quebra de
propósito aquilo que cada checagem protege — faz o vizinho ganhar do projeto
aberto, remove uma camada, desliga o fatiamento, esvazia o detector de segredo —
e **falha se as checagens não perceberem**. Checagem que só passou não é prova;
ela ficaria verde numa regressão de verdade também.

As duas suítes acharam defeitos reais durante o desenvolvimento, incluindo uma
trava que morria na primeira vez que tentou recusar algo, e um backup que
devolvia os arquivos 38 bytes maiores do que os guardou.

O CI roda tudo no Linux, macOS e Windows, em Python 3.8 e 3.12.

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

Markdown puro, que você lê, edita, move ou apaga. Remover a ferramenta não remove
a memória.

---

## Honestamente: usar isto ou o claude-mem?

Este projeto nasceu estudando o
[claude-mem](https://github.com/thedotmack/claude-mem), e ele continua sendo a
alternativa séria. Conferido hoje, não lembrado:

| | claude-mem | este |
|---|---|---|
| usuários | **93 mil estrelas** | **0** — ninguém além do autor rodou |
| arquitetura | serviço local, SQLite, banco vetorial Chroma | 6 scripts Python e arquivos Markdown |
| o que precisa instalar | Node 20+, Bun, uv | Python 3.8 |
| busca | híbrida: semântica + palavra | **só léxica** |
| custo | camada grátis, com assinatura paga para memória hospedada | nenhum, nunca |
| agentes | Claude Code e vários outros | só Claude Code |
| testes / CI declarados | não constam no README | 75 checagens, mutação, 6 ambientes |
| traz um método funcionando | não | 6 travas que recusam |
| traz lições | não | 56 notas |

**Use o claude-mem se** você quer busca semântica, usa agentes além do Claude
Code, ou prefere depender de algo que milhares de pessoas rodam. São bons
motivos, e este projeto não vence nenhum deles.

**Use este se** você não quer nada rodando para manter, nada para pagar,
resultados que consegue explicar, e notas num formato que ainda abre daqui a dez
anos — ou se o que você quer é o `method/` e o `knowledge/`, que não têm
equivalente lá.

### A troca, dita na cara

**Busca léxica, não semântica.** Se você perguntar por "autenticação" e a nota
disser "login", o BM25 não liga as duas; um banco vetorial ligaria.

Essa lacuna foi **medida aqui**, não presumida. Os vetores foram construídos,
testados e **reprovados** — ganho real (19 para 23 de 32) que mesmo assim não
justificava trocar um sistema autossuficiente de 114 ms por um que exige servidor
de modelo local, porque o log de uso real mostrou que o buraco era 5,8%, e não os
81% que um teste de estresse feito para a ocasião sugeria. O raciocínio e a
condição que reabre isso estão em
[`engine/docs/MEASUREMENTS.md`](engine/docs/MEASUREMENTS.md).

**Zero usuários é um fato real deste projeto, não modéstia.** Ele funciona, está
testado, e ninguém o submeteu a uma instalação que não seja a do autor.

---

## Licença

MIT — veja [LICENSE](LICENSE). Faça o que quiser com isto.

Também aqui: [CHANGELOG](CHANGELOG.md) · [SECURITY](SECURITY.md) ·
[CLAUDE.md](CLAUDE.md), que dá ao seu assistente o contexto deste repositório no
instante em que você o abre — a mesma coisa que o projeto faz pelo seu trabalho.
