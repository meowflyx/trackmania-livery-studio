# Optional official-directory submission

Publishing this GitHub repository is **not** publication in the official OpenAI plugin directory. No official-directory submission, acceptance or publisher verification is claimed.

This project currently packages a skills-only plugin with `requires_local_executor=true`. It uses local Windows texconv and does not contain a local MCP server. Do not add a dummy MCP server just to submit it.

For a future submission:

1. Confirm submission access and the publishing individual/business identity in the OpenAI portal.
2. Finish the documented clean desktop and actual game tests for the released package; keep honest support/platform requirements.
3. Use the **plugin ZIP** (plugin.json at archive root), not the marketplace ZIP or generated car skin ZIP.
4. Review current skills-only metadata, assets, automated scans and desktop-only requirements; resolve actual portal findings.
5. Submit for review, then publish only after approval and an explicit publisher decision.

Do not invent support/privacy/terms URLs or claim an approval that has not occurred. The repository provides public documentation and an issue tracker; add any additional publisher information through the real publisher's workflow. Skills-only eligibility can vary; the portal determines access. Local-MCP partner eligibility requirements should not be silently conflated with a skills-only package that has no MCP server.

Primary sources checked during preparation:
- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/plugins/deploy/desktop-only
- https://developers.openai.com/plugins/plugin-guidelines
- https://developers.openai.com/plugins/build/plugins
