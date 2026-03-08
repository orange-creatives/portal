const { chromium } = require('C:/Users/orang/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright-core');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Users/orang/AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe',
  });
  const page = await browser.newPage();

  await page.setViewportSize({ width: 700, height: 900 });

  const htmlPath = 'E:/orange-creatives/portal/docs/drafts/zenn-format-test/pattern-d-source.html';
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'));

  // Wait for fonts to load
  await page.waitForTimeout(500);

  // Get the actual height of the body content
  const bodyHeight = await page.evaluate(() => {
    return document.body.scrollHeight;
  });

  await page.setViewportSize({ width: 700, height: bodyHeight });

  const outputPath = 'E:/orange-creatives/portal/docs/drafts/zenn-format-test/pattern-d.png';
  await page.screenshot({
    path: outputPath,
    fullPage: true,
  });

  console.log('Screenshot saved to:', outputPath);
  await browser.close();
})();
