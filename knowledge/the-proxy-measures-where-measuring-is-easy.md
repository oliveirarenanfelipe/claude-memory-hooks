---
name: the-proxy-measures-where-measuring-is-easy
description: When the real thing is hard to observe, a proxy gets used — and proxies are chosen for convenience, not fidelity. Every local fix to a proxy makes the gap harder to see.
scope: global
type: concept
---

# The proxy measures where measuring is easy

**The rule.** When the thing you care about is hard to observe, something easier
gets measured in its place. The proxy is chosen for **convenience**, not fidelity,
and then it quietly becomes the definition.

## The shape of the failure

You want to know how many people joined a group. That is awkward to query, so the
count uses "people who clicked the join link" — which is available, adjacent, and
usually close.

Then the two diverge: the link starts being shared, or joining starts failing
silently. The reported number stays plausible and stops being true. Each time
someone notices a discrepancy, a local correction is applied to the proxy, which
makes it more accurate in that one case and **harder to recognise as a proxy at
all**.

*(Illustrative case.)*

## The tell

**You are patching the proxy for the third time.** Each patch is small and
justified; together they are a system maintaining an approximation of something it
could measure directly if anyone re-asked the question.

## The two questions

1. **What is the real quantity**, stated plainly? Write it down. Often nobody has,
   and the proxy has been the definition for so long that the answer is genuinely
   unclear.
2. **What would it cost to measure it directly, today?** The original reason for
   the proxy is often years old. The direct measurement that was impossible then
   is frequently a single query now.

## When the proxy stays

Sometimes direct measurement really is out of reach. Then the rule is naming:
**call the metric what it measures**, not what you wish it measured. "Link
clicks" is honest and nobody builds a decision on it believing it is membership.
A field called `members` will be trusted forever.
