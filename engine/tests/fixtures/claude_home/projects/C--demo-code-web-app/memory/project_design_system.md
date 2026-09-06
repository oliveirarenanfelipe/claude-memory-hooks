---
name: Design system tokens
description: Colour, spacing and typography tokens, and the dark mode contract
type: project
---

Colours are defined once as tokens on the root element and redefined only inside
the dark mode block. A component never hardcodes a hex value.

## Dark mode
Three states: explicit light, explicit dark, and system. A colour that is only
defined inside a media query is a bug, because the explicit toggle then has
nothing to override.
