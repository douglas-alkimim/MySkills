# Extending WOP to New Domains

Add a domain module only when recurring specialist decisions cannot be handled by the core method. Follow specifications/module-contract.md.

A module inherits all WOP principles and must define activation, exclusions, required inputs, decision rules, risks, additional plan fields, verification, acceptance, and optional submodule routing. It must not weaken the strict wave barrier, replace core statuses, duplicate generic planning guidance, or assume authorization for domain actions.

Candidate domains include research, data analysis, design, infrastructure, business, operations, and education. Keep each module independent and load it only when applicable.
