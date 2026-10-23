# Hosts and installation

Primary target: ChatGPT desktop Work/Codex with local execution, browsing and native image generation. This skills-only plugin declares `requires_local_executor=true`; it does not supply or unlock those tools. No login/backend/API key is added by the package. Windows ships texconv x64; another OS needs an equivalent compatible native encoder explicitly supplied with `--texconv`. Python dependencies are listed in scripts/requirements.txt.

After plugin installation, select **Trackmania Livery Studio** from the `@` menu in a new Work chat. Typing a plain string without selecting a registered entry does not install or activate a plugin. CLI uses `$trackmania-livery-studio`. A raw SKILL.md can guide another agent, but needs its resources, file execution, compatible encoder and image-generation facility to complete the full pipeline.

For local distribution, extract the **marketplace ZIP**, register that extracted directory with `codex plugin marketplace add PATH --json`, then `codex plugin add trackmania-livery-studio@trackmania-livery-studio --json`. Check `codex plugin list --json`. Restart the desktop app to refresh plugin discovery if needed. Do not install a duplicate standalone skill alongside the bundled plugin skill.

The independent **plugin ZIP** has plugin.json at archive root for compatible import/publication flows. It is not the same archive as a skin ZIP. This project does not publish anything to a public directory or workspace. Cloud/web availability and marketplace publication require the respective platform's supported administration flow; local install is not global cloud publication.

Standalone Agent Skills folder is skills/trackmania-livery-studio. It uses standard SKILL.md and optional agents/openai.yaml. Claude Code compatibility manifest is included, but cross-host runtime/tool availability must be tested on that host; the Windows export tests do not establish Claude/cloud execution.
