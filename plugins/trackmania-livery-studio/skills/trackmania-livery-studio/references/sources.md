# Sources and maintenance

Checked 2026-10-23. These are primary documentation and an explicitly labelled archived developer post, not SEO recipes. Recheck host format/current game requirements when upgrading. No account configuration or conversation history is required to use this package.

## Skill/plugin design

- OpenAI, [package your plugin](https://developers.openai.com/plugins/build/plugins): portable root manifest, skill directories, local marketplace and installed cache semantics. This package keeps host metadata separate from portable instructions.
- OpenAI, [build plugins](https://learn.chatgpt.com/docs/build-plugins): selecting an installed plugin through the @ menu in Chat/Work. An installation is not proven merely by displaying a prompt.
- OpenAI, [build skills](https://learn.chatgpt.com/docs/build-skills): reusable instruction/resource packages and explicit invocation.
- OpenAI, [desktop-only](https://developers.openai.com/plugins/deploy/desktop-only): local executor declaration for bundled native execution.
- [Agent Skills specification](https://agentskills.io/specification): SKILL.md frontmatter and portable directory layout.
- Anthropic engineering, [equipping agents with skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills): progressive disclosure of instructions, executable resources and assets.
- Anthropic, [authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): concise routing, deterministic scripts, realistic evaluation instead of instruction-wording tests. The release tests cover observable package and pipeline behavior; they do not claim all models were evaluated.

## Texture pipeline

- Archived **Nadeo/Ubi-Alinoa** resource post, [Stadium car resources](https://devtrackers.gg/trackmania/p/3490d99c-stadium-car-ressources-all-you-need-to-create-skins-for-the-stadium-cars): historical car texture names, BC1/BC5 and special data-map roles. It is a mirror of a 2020 developer post, not a newly published official spec.
- Nadeo [texture mod guidance](https://doc.trackmania.com/create/texture-mods/mods/): DDS/mipmap background. This page concerns map mods; its directory rules and size recommendations are not asserted as car ZIP requirements.
- Microsoft [texconv](https://github.com/microsoft/DirectXTex/wiki/Texconv): DDS encoder options. The included MIT executable is pinned by SHA in package asset manifest; upgrades require repeating orientation/channel/mip tests.
- Three.js [DDSLoader](https://github.com/mrdoob/three.js/blob/r180/examples/jsm/loaders/DDSLoader.js): native colour mip-chain preview. MIT notice included. Approximate PBR is explicitly not the game's shader.
- [Community preview mesh](https://sketchfab.com/3d-models/trackmania-2020-carsport-c8b80bfc1ed1427eb37f3eba8d1ecfbf), amogusstrikesback2, CC BY 4.0; attribution and original license bundled. Obtained through [TM-LiveSync](https://github.com/LovelyPotato-ai/TM-LiveSync). Not an official Nadeo template.

Our prior skin iterations supplied regression scenarios: mip0-only renderer mismatch, thin-keyline BC1 artifacts, moving wing interference, cropped logos and incorrect inference from small screenshots. Those observations become conditional tests and decision guidance, not mandatory styling for every user.
