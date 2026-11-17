# Parallelism

Parallelism is useful only when it shortens the critical path without adding unsafe coordination. WOP optimizes useful independent work, not item or agent count.

Permit same-wave concurrency when:

- all required inputs exist before the wave;
- ownership boundaries are disjoint or isolation is explicit;
- no item needs another same-wave output or decision;
- shared services tolerate the combined operations;
- acceptance can be evaluated independently before integration; and
- integration is deterministic and included in the wave gate.

Prefer sequential work when tasks edit one contract, depend on evolving judgment, compete for an exclusive environment, or require continuous mutual feedback.

For multiple agents, assign one owner per item, state allowed files and effects, prohibit cross-ownership edits, require structured reports, and integrate only after all reports arrive. Consider dispatch, synchronization, review, and integration cost before adding an agent. The objective is the smallest safe critical path, not maximum agent utilization.

Before splitting, ask: “Does splitting this work create genuinely independent execution, improve verification, or reduce risk?” If not, retain one item. Keep dependent or continuously coordinated actions together unless a real prerequisite or interference conflict requires another wave.
