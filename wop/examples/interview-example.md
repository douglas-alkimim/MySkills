# Example: Question Frontier

Loose request: “Plan a customer export feature.”

Repository inspection answers the framework, existing customer schema, job system, and storage provider. The remaining decision graph is:

- D001: who may request an export.
- D002: delivery channel, dependent on D001 and data sensitivity.
- D003: retention period, dependent on delivery and compliance policy.
- D004: synchronous or background behavior, informed by measured export size.

First frontier:

“Which roles may request an export, and may they export only their own tenant? This determines the authorization boundary.”

After D001, ask D002 with feasible delivery choices and risks. Do not ask retention before the delivery and policy constraints are known.

D004 is partly empirical. Add a discovery item to measure representative export volume and duration rather than asking the user to guess. If delivery experience is hard to choose abstractly, plan a narrow prototype with explicit observations.

Record each answer in Decisions and update requirements, risks, and criteria. Stop interviewing when every material branch is decided, discoverable, prototyped, or explicitly deferred.
