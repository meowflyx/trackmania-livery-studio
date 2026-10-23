/** Capture observable native-DDS viewer evidence; does not validate game shaders. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.STUDIO_PLAYWRIGHT || 'playwright');

async function main() {
  const [url, output] = process.argv.slice(2);
  if (!url || !output) throw new Error('Usage: node capture.cjs http://127.0.0.1:PORT/path/viewer.html OUTPUT_DIRECTORY');
  const parsed = new URL(url);
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(parsed.hostname)) throw new Error('Use a loopback preview URL');
  fs.mkdirSync(output, {recursive: true});
  const errors = [];
  const browser = await chromium.launch({channel: process.env.STUDIO_BROWSER_CHANNEL || undefined, headless: true, args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({viewport: {width: 1200, height: 800}, deviceScaleFactor: 1});
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
    const info = [];
    parsed.search = 'capture=1';
    await page.goto(parsed.href, {waitUntil: 'networkidle'});
    await page.waitForFunction(() => window.viewerReady === true, null, {timeout: 60000});
    info.push(await page.evaluate(() => window.viewerInfo));
    for (let angle = 0; angle < 360; angle += 30) {
      await page.evaluate(value => window.setAngle(value), angle);
      await page.waitForTimeout(150);
      await page.screenshot({path: path.join(output, `unlit_${String(angle).padStart(3, '0')}.png`)});
    }
    parsed.search = 'capture=1&lit=1';
    await page.goto(parsed.href, {waitUntil: 'networkidle'});
    await page.waitForFunction(() => window.viewerReady === true, null, {timeout: 60000});
    info.push(await page.evaluate(() => window.viewerInfo));
    for (const view of ['hero', 'rear', 'front', 'back', 'left', 'side', 'top', 'chase', 'wheel']) {
      await page.evaluate(value => window.setView(value), view);
      await page.waitForTimeout(150);
      await page.screenshot({path: path.join(output, `lit_${view}.png`)});
    }
    const record = {status: errors.length ? 'VIEWER_FAILED' : 'VIEWER_CAPTURED', errors,
      captures: 21, info, game: 'GAME_PENDING', visualInspection: 'PENDING'};
    fs.writeFileSync(path.join(output, 'capture.json'), JSON.stringify(record, null, 2));
    if (errors.length) throw new Error(JSON.stringify(errors));
    if (info.some(item => item.generateMipmaps !== false || !item.mips.Skin)) throw new Error('Native DDS evidence missing');
    console.log('CAPTURE_OK: 21 views; native compressed colour mips; no browser errors; visual/game inspection separate');
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
