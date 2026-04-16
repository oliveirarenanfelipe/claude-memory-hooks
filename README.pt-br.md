# claude-memory-hooks

> Claude Code que lembra de tudo. Sem servidor. Sem banco de dados. Sem custo.

[Read in English](README.md)

---

## O problema

Se você usa o Claude Code de verdade, já bateu nessas paredes:

1. **Claude esquece tudo entre sessões** — você explica o mesmo contexto várias vezes
2. **Vários projetos, sem continuidade** — trocar de projeto significa começar do zero
3. **Trabalho some quando não salva** — fecha a sessão e o raciocínio por trás das decisões vai junto

---

## O que isso faz

Três hooks leves que rodam em silêncio dentro do Claude Code:

| Hook | Quando | O que faz |
|---|---|---|
| `session_context.py` | Sessão abre | Injeta o brief da última sessão no contexto do Claude |
| `prompt_memory.py` | Você digita um prompt | Detecta o assunto e injeta a memória relevante |
| `auto_brief.py` | Sessão fecha | Lê a conversa e salva um brief automaticamente |

**Sem chamadas de LLM. Sem API key. Sem serviços externos. Só Python e arquivos Markdown.**

A memória fica em arquivos `.md` simples que você pode ler, editar ou apagar quando quiser.

---

## Como fica na prática

**Antes:**
> Você: "Então continuando de ontem, a gente estava no webhook de pagamento onde o erro era—"
> Claude: "Não tenho contexto de sessões anteriores..."

**Depois:**
> *(Sessão abre)*
> Claude já sabe: nome do projeto, última tarefa, próximo passo, bloqueios ativos.
> Você... simplesmente continua.

---

## Instalação

**Requisitos:** Python 3.8+, Claude Code

```bash
git clone https://github.com/oliveirarenanfelipe/claude-memory-hooks
cd claude-memory-hooks
bash install.sh
```

Depois abra o Claude Code e rode:

```
/memory-setup
```

O Claude vai te fazer algumas perguntas sobre seus projetos e configurar tudo.

---

## Como é o setup

`/memory-setup` é uma conversa guiada — sem arquivos de configuração para editar na mão:

```
Claude: Quantos projetos você trabalha no Claude Code?
Você: Três — meu produto SaaS, um site de cliente, e meu projeto de conteúdo

Claude: Onde fica o seu produto SaaS no computador?
Você: C:\Users\eu\Projetos\meu-saas

Claude: Que palavras você costuma digitar quando fala sobre ele?
Você: dashboard, cobrança, usuários, stripe

[repete para cada projeto]

Claude: Pronto. A partir de agora vou lembrar donde você parou.
```

---

## O que é salvo

No final de cada sessão, um brief é criado automaticamente em:

```
~/.claude/projects/<seu-projeto>/memory/session_briefs/<projeto>.md
```

```markdown
**Data:** 2025-01-15
**Projeto:** meu-saas

**O que foi feito:** Implementei o handler do webhook Stripe para cancelamentos de assinatura.
**Arquivos tocados:** `webhooks/stripe.py`, `models/subscription.py`
**Próximo passo:** Testar o fluxo de cancelamento end-to-end com o Stripe CLI
**Bloqueio:** Nenhum.
```

Legível por humanos. Editável. Seu.

---

## Touch points

O sistema roda em silêncio mas avisa que está funcionando:

- `📝 Brief salvo — nome-do-projeto` — aparece quando o brief é salvo
- Contexto é injetado automaticamente quando a sessão abre (você vai perceber que o Claude já sabe das coisas)

---

## Filosofia

Isso foi construído estudando o [claude-mem](https://github.com/thedotmack/claude-mem) — um sistema de memória popular com 58k estrelas.

A diferença: o claude-mem roda um servidor local persistente, usa SQLite, ChromaDB para busca semântica, e tem uma arquitetura complexa de workers. É poderoso.

Este projeto faz a mesma função central com três scripts Python e arquivos Markdown. Nada para manter rodando. Nada para quebrar.

O insight central: os hooks do Claude Code podem retornar `hookSpecificOutput.additionalContext` — qualquer texto que você colocar lá é injetado no contexto do Claude. Esse é o mecanismo inteiro.

---

## Licença

MIT — faça o que quiser.
