---
name: a-buffered-source-looks-more-reliable-than-it-is
description: Comparing the availability of two sources only means something if they transmit the same way. A source with memory retransmits after an outage and looks flawless; a real-time one just has a hole.
scope: global
type: concept
---

# A buffered source looks more reliable than it is

**The rule.** Comparing the **availability** of two data sources is only meaningful
if they transmit the same way. A source that buffers locally and retransmits after
an outage shows a complete record. A source that transmits in real time shows a
gap for the same outage.

Same network, same failure, opposite-looking reliability.

## The shape of the failure

Two devices report to the same collector. One shows 99.8% coverage over a month;
the other shows 94%. The obvious conclusion is that the second is faulty, and a
replacement is planned.

Both experienced the same connectivity interruptions. The first has onboard
storage and sent everything once the link returned. The second has none, so those
minutes are simply absent.

The measurement was of **buffering**, not of reliability, and the decision it drove
was to replace the working device.

*(Illustrative case.)*

## The question that makes the comparison valid

> **"When the link drops, does this source keep the data and send it later, or is
> it lost?"**

Until you can answer that for both, an availability comparison says nothing about
either.

## The correction

Compare **what each source could have produced**, not what arrived. For a buffered
source, the gap is invisible in the data and must be found elsewhere — in the
connectivity log, or in the timestamps of arrival versus measurement.

Arrival time and measurement time being far apart is the fingerprint of buffering,
and it is usually available and never looked at.

## The general form

**Any metric computed on delivered data measures delivery as much as it measures
the phenomenon.** Whenever two things are compared and one has a recovery
mechanism the other lacks, the comparison is about the mechanism.
