---
name: memory-setup
description: Configure claude-memory-hooks for your projects. Run this once after installing.
---

You are setting up claude-memory-hooks for this user.
Your job is to have a friendly conversation, understand their setup, and generate the config file.

---

## The conversation

Greet them briefly and explain what you're doing in one sentence.

Then ask these questions, **one at a time**, waiting for each answer:

**1. Projects**
"How many projects do you work on with Claude Code? Give me the names — can be anything, doesn't need to be technical."

*(Wait for answer. If they list more than one, that's great. If they say "just one", that's fine too.)*

**2. Paths** (for each project they named)
"Where does [project name] live on your computer? Just paste the folder path."

*(They can find this by opening the folder and copying from the address bar. Help them if needed.)*

**3. Keywords** (for each project)
"What words would you typically type when talking to Claude about [project name]? Think about client names, product names, tools you use, or topics you return to often."

*(Examples to help them: "For a bakery client it might be 'bakery', 'Maria', 'website'. For a software product it might be 'dashboard', 'users', 'billing'.)*

**4. Language preference**
"Do you want the memory briefs in English or Portuguese (PT-BR)?"

---

## After collecting answers

Generate the config file at `~/.claude/memory-hooks/config.json`:

```json
{
  "language": "en",
  "projects": [
    {
      "name": "Project Name",
      "slug": "project-name",
      "path": "/path/to/project",
      "keywords": ["word1", "word2", "word3"]
    }
  ]
}
```

Rules:
- `slug`: lowercase, hyphens, no spaces (derive from name)
- `path`: exactly what they gave you
- `keywords`: what they said + obvious variations (singular/plural, abbreviations)
- `language`: "en" or "pt-br"

Write the file using the Write tool.

---

## Confirm and close

Show them a summary of what was configured:

"All set. Here's what I configured:

**[Project name]** — [path]
Keywords: [word1], [word2], [word3]

From now on:
- When you open Claude in this project, I'll automatically know where you left off
- When you mention [keyword], I'll bring up the relevant context
- When you close a session, I'll save a brief of what we did

You don't need to do anything else. Just work normally."

---

## If they want to add more projects later

Tell them: "Just run /memory-setup again — I'll update the config."
