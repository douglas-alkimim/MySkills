# MySkills

This is my personal collection of skills, tools, and experiments for making AI-assisted work more useful. I keep the things I build and refine for software development, research, planning, automation, productivity, and whatever else turns out to be helpful.

Each skill is self-contained and can be installed or used independently. Feel free to explore them, adapt them to your own workflow, or just borrow the parts that are useful.

## Skills

### [WOP — Wave-Oriented Planning](wop/)

WOP helps me turn a project into a durable execution plan made of strictly ordered waves. Work inside a wave can run in parallel when it is genuinely independent, while dependencies, acceptance criteria, evidence, and handoffs stay explicit.

It includes templates, planning guidance, validation scripts, lifecycle tooling, and examples. The Python tools use only the standard library.

### [Google AI Ecosystem](google-ai-ecosystem/)

Google AI Ecosystem gives me one place to route work between Google Antigravity CLI and Gemini Web. Antigravity is the repository-engineering route; Gemini is the research and media route, with a bundled MCP component for browser-based Gemini workflows.

The bundled Gemini MCP contains modified third-party MIT-licensed code. Its original notice and technical provenance stay with the component in [`vendor/gemini-mcp`](google-ai-ecosystem/vendor/gemini-mcp/).

## Installing a skill

Clone or download this repository, then copy the complete skill directory into the skills directory used by your agent host. Keep the directory structure intact:

```text
<your-skill-directory>/wop/
<your-skill-directory>/google-ai-ecosystem/
```

WOP requires Python 3.9 or newer and has no third-party Python dependencies. Google AI Ecosystem has additional Node.js, pnpm, browser, and component-specific setup; its [installation guide](google-ai-ecosystem/references/installation.md) walks through the preflight and install flow.

This repository will keep changing as I create new skills, improve existing ones, and retire ideas that are no longer useful.

## License

My original work in this repository is available under the [MIT License](LICENSE). Vendored or derived third-party components retain their own copyright notices, license files, and provenance metadata; see the [Gemini MCP license](google-ai-ecosystem/vendor/gemini-mcp/LICENSE) and [`VENDOR.json`](google-ai-ecosystem/vendor/gemini-mcp/VENDOR.json).
