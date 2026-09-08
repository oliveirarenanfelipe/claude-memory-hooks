---
name: the-first-case-becomes-the-default-silently
description: Opening a system to a second variant — another tenant, region, plan — does not leave the unparameterised parts empty. They answer with the FIRST case's rules, quietly and confidently.
scope: global
type: concept
---

# The first case becomes the default, silently

**The rule.** When a system built for one case is opened to a second — another
customer, region, tenant, plan — the parts nobody parameterised do not become
empty or throw. They **keep answering with the first case's rules**, confidently
and with no indication that they are doing so.

## The shape of the failure

A calculation is built for one jurisdiction. A second is added, and the obvious
differences are parameterised: rates, labels, formats.

A rounding rule, a cutoff date and a threshold were never parameters — they were
constants, correct for the original case and invisible as choices. The second
jurisdiction gets the first one's rules for all three. Every output is plausible;
some are wrong.

Nothing is missing, so nothing reports missing.

*(Illustrative case.)*

## Why this is hard to find by reading

An unparameterised constant does not look like a gap. It looks like a value. To
notice it you have to already be asking *"is this the same for everyone?"* about
each line — which is exactly the question that gets asked about the values that
were parameterised and not about the ones that were not.

## The practice, before opening to the second case

**Inventory the constants, not the parameters.** Grep for literal numbers, dates,
strings and thresholds in the code path. For each, answer explicitly: universal,
or first-case-specific? Write the answer down next to it.

The exercise is tedious and it is the whole job. The parameters were always going
to get attention; the constants are where the second case breaks.

## The strong version

**Add the second case with the first case's constants deliberately removed** — set
them to a value that fails loudly. Everything that breaks was first-case
knowledge, and it breaks now instead of in production.
