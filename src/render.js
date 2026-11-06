// Render diwali.html frame-by-frame and pipe PNGs into ffmpeg.
// Usage: node render.js out.mp4 [--preview f1,f2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const out = process.argv[2] || path.join(__dirname, '..', 'video', 'silent.mp4');
const previewIdx = process.argv.indexOf('--preview');
const preview = previewIdx > 0 ? process.argv[previewIdx + 1].split(',').map(Number) : null;

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'diwali.html'));
  await page.evaluate(() => window.ready);
  const frames = await page.evaluate(() => window.FRAMES);

  let ff = null;
  if (!preview) {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  }
  const last = preview ? Math.max(...preview) : frames - 1;
  const t0 = Date.now();
  for (let i = 0; i <= last; i++) {
    const want = !preview || preview.includes(i);
    const data = await page.evaluate(([i, want]) => { window.renderFrame(i); return want ? document.getElementById('c').toDataURL('image/png') : null; }, [i, want]);
    if (!want) continue;
    const buf = Buffer.from(data.split(',')[1], 'base64');
    if (preview) fs.writeFileSync(path.join(process.env.PREVIEW_DIR || '.', `frame_${String(i).padStart(3, '0')}.png`), buf);
    else if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log('frame', i, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  const sched = await page.evaluate(() => window.getSchedule());
  fs.writeFileSync(path.join(__dirname, 'schedule.json'), JSON.stringify(sched, null, 1));
  await browser.close();
  if (ff) { ff.stdin.end(); await new Promise(r => ff.on('close', r)); }
  console.log('done', out);
})();
