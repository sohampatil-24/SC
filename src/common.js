// Shared engine for the festival greeting videos (1080x1920 @ 30fps).
const W = 1080, H = 1920, FPS = 30, DT = 1 / FPS;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

// ---------- helpers ----------
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
let rnd = mulberry32(1);
function seed(s) { rnd = mulberry32(s); }
const R = (a, b) => a + (b - a) * rnd();
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const easeOutCubic = x => 1 - Math.pow(1 - x, 3);
const easeInCubic = x => x * x * x;
const easeInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOutBack = x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, x) => a + (b - a) * x;
function layer() { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; }
const schedule = { launches: [], bursts: [], events: {} };

function glow(x, y, r, color, g = ctx) {
  const rg = g.createRadialGradient(x, y, 0, x, y, r);
  rg.addColorStop(0, color); rg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = rg; g.beginPath(); g.arc(x, y, r, 0, 6.28); g.fill();
}

// ---------- fireworks ----------
const Fireworks = (() => {
  const fw = layer(), fx = fw.getContext('2d');
  const particles = [], rockets = [], flashes = [], plan = [];
  const RISE = 0.9;
  function add(t, x, y, type, hue) { plan.push({ t, x, y, type, hue, launched: false }); }
  function explode(b, t) {
    const n = b.type === 'willow' ? 150 : b.type === 'ring' ? 110 : 170;
    const speed = b.type === 'willow' ? 430 : b.type === 'ring' ? 520 : 560;
    const tilt = R(0, Math.PI);
    for (let i = 0; i < n; i++) {
      let vx, vy;
      if (b.type === 'ring') {
        const a = i / n * Math.PI * 2; vx = Math.cos(a) * speed; vy = Math.sin(a) * speed * 0.55;
        const c = Math.cos(tilt), s = Math.sin(tilt); [vx, vy] = [vx * c - vy * s, vx * s + vy * c];
      } else { const a = R(0, 6.283), m = 0.6 + 0.4 * rnd(); vx = Math.cos(a) * speed * m; vy = Math.sin(a) * speed * m; }
      particles.push({ x: b.x, y: b.y, px: b.x, py: b.y, vx, vy, life: b.type === 'willow' ? R(1.8, 2.6) : R(1.1, 1.7), age: 0,
        hue: b.hue + R(-12, 12), sat: b.type === 'willow' ? 90 : 100, light: b.type === 'willow' ? 62 : 64,
        drag: b.type === 'willow' ? 2.6 : 1.9, g: b.type === 'willow' ? 160 : 120, glitter: b.type === 'willow' || rnd() < .25, w: b.type === 'willow' ? 2.2 : 3 });
    }
    for (let i = 0; i < 40; i++) { const a = R(0, 6.28), m = R(40, 200); particles.push({ x: b.x, y: b.y, px: b.x, py: b.y, vx: Math.cos(a) * m, vy: Math.sin(a) * m, life: R(.3, .6), age: 0, hue: 50, sat: 100, light: 92, drag: 3, g: 60, glitter: false, w: 3 }); }
    flashes.push({ x: b.x, y: b.y, hue: b.hue, t0: t });
    schedule.bursts.push({ t: +t.toFixed(3), type: b.type, x: b.x / W, y: b.y / H });
  }
  function step(t) {
    for (const b of plan) if (!b.launched && t >= b.t - RISE) {
      b.launched = true; const sx = b.x + R(-120, 120);
      rockets.push({ b, sx, sy: H - 260, t0: t, px: sx, py: H - 260 });
      schedule.launches.push({ t: +t.toFixed(3), x: b.x / W });
    }
    fx.globalCompositeOperation = 'destination-out'; fx.fillStyle = 'rgba(0,0,0,0.24)'; fx.fillRect(0, 0, W, H);
    fx.globalCompositeOperation = 'lighter'; fx.lineCap = 'round';
    for (let i = rockets.length - 1; i >= 0; i--) {
      const r = rockets[i], u = clamp((t - r.t0) / RISE), e = easeOutCubic(u);
      const x = lerp(r.sx, r.b.x, e), y = lerp(r.sy, r.b.y, e);
      fx.strokeStyle = 'hsla(40,100%,75%,0.95)'; fx.lineWidth = 4;
      fx.beginPath(); fx.moveTo(r.px, r.py); fx.lineTo(x, y); fx.stroke();
      for (let k = 0; k < 2; k++) particles.push({ x, y, px: x, py: y, vx: R(-40, 40), vy: R(20, 90), life: R(.25, .5), age: 0, hue: 35, sat: 100, light: 70, drag: 2, g: 80, glitter: true, w: 2 });
      r.px = x; r.py = y;
      if (u >= 1) { rockets.splice(i, 1); explode(r.b, t); }
    }
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i]; p.age += DT;
      if (p.age > p.life) { particles.splice(i, 1); continue; }
      const k = Math.exp(-p.drag * DT); p.vx *= k; p.vy = p.vy * k + p.g * DT;
      p.px = p.x; p.py = p.y; p.x += p.vx * DT; p.y += p.vy * DT;
      const u = p.age / p.life; let a = 1 - u * u;
      if (p.glitter && u > .35) a *= rnd() < .5 ? 1 : 0.15;
      fx.strokeStyle = `hsla(${p.hue},${p.sat}%,${p.light + (1 - u) * 12}%,${a})`; fx.lineWidth = p.w * (1 - u * .5);
      fx.beginPath(); fx.moveTo(p.px, p.py); fx.lineTo(p.x, p.y); fx.stroke();
    }
    fx.globalCompositeOperation = 'source-over';
  }
  function drawFlashes(t, strength = .45) {
    ctx.globalCompositeOperation = 'lighter';
    for (const f of flashes) {
      const age = t - f.t0; if (age < 0 || age > 1.2) continue;
      const rg = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, 700);
      rg.addColorStop(0, `hsla(${f.hue},90%,60%,${Math.exp(-age * 4) * strength})`); rg.addColorStop(1, 'hsla(0,0%,0%,0)');
      ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    }
    ctx.globalCompositeOperation = 'source-over';
  }
  return { add, step, drawFlashes, canvas: fw };
})();

// ---------- decorative pieces ----------
function drawDiya(x, y, s, t, sd) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const fl = 1 + 0.12 * Math.sin(t * 17 + sd) + 0.08 * Math.sin(t * 31 + sd * 2);
  ctx.globalCompositeOperation = 'lighter'; glow(0, -48, 120 * fl, 'rgba(255,150,40,.45)'); ctx.globalCompositeOperation = 'source-over';
  const g = ctx.createLinearGradient(0, -20, 0, 34); g.addColorStop(0, '#e0702a'); g.addColorStop(1, '#7a2c0c');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(-62, -12); ctx.quadraticCurveTo(-56, 34, 0, 36); ctx.quadraticCurveTo(56, 34, 62, -12);
  ctx.quadraticCurveTo(76, -20, 84, -26); ctx.quadraticCurveTo(60, -6, 0, -8); ctx.quadraticCurveTo(-40, -8, -62, -12); ctx.fill();
  ctx.fillStyle = '#ffcf5a'; for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.arc(i * 14, 14 - Math.abs(i) * 1.5, 3.2, 0, 6.28); ctx.fill(); }
  ctx.beginPath(); ctx.ellipse(0, -10, 56, 7, 0, 0, 6.28); ctx.fillStyle = '#5a1e08'; ctx.fill();
  ctx.save(); ctx.translate(-6, -14); ctx.rotate(0.06 * Math.sin(t * 7 + sd)); ctx.scale(1, fl);
  const fg = ctx.createRadialGradient(0, -14, 2, 0, -18, 34);
  fg.addColorStop(0, '#ffffff'); fg.addColorStop(.3, '#fff1a0'); fg.addColorStop(.7, '#ff9a1a'); fg.addColorStop(1, 'rgba(255,60,0,0)');
  ctx.fillStyle = fg; ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(-18, -8, -14, -34, 0, -62); ctx.bezierCurveTo(14, -34, 18, -8, 0, 0); ctx.fill();
  ctx.restore(); ctx.restore();
}
function swastik(x, y, s, color, lw) {
  ctx.save(); ctx.translate(x, y); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'square';
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(0, -s); ctx.lineTo(s, -s);
  ctx.moveTo(0, 0); ctx.lineTo(s, 0); ctx.lineTo(s, s);
  ctx.moveTo(0, 0); ctx.lineTo(0, s); ctx.lineTo(-s, s);
  ctx.moveTo(0, 0); ctx.lineTo(-s, 0); ctx.lineTo(-s, -s);
  ctx.stroke();
  for (const [dx, dy] of [[.5, -.5], [.5, .5], [-.5, .5], [-.5, -.5]]) { ctx.beginPath(); ctx.arc(dx * s, dy * s, lw * .75, 0, 6.28); ctx.fill(); }
  ctx.restore();
}
function drawRangoli(x, y, R0, rot, a) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot);
  const rings = [[16, R0, '#ff2d7a'], [16, R0 * .82, '#ff9a1a'], [12, R0 * .64, '#ffd23a'], [12, R0 * .48, '#1fc8b4'], [8, R0 * .32, '#b04bff']];
  rings.forEach(([n, r, c], k) => {
    for (let i = 0; i < n; i++) {
      ctx.save(); ctx.rotate(i / n * 6.28 + k * .2); ctx.fillStyle = c;
      ctx.beginPath(); ctx.moveTo(0, -r * .55); ctx.quadraticCurveTo(r * .2, -r * .8, 0, -r); ctx.quadraticCurveTo(-r * .2, -r * .8, 0, -r * .55); ctx.fill();
      ctx.fillStyle = '#fff4d6'; ctx.beginPath(); ctx.arc(0, -r * 1.04, 5, 0, 6.28); ctx.fill();
      ctx.restore();
    }
  });
  ctx.fillStyle = '#ffd23a'; ctx.beginPath(); ctx.arc(0, 0, R0 * .14, 0, 6.28); ctx.fill();
  ctx.restore();
}
function lightRays(x, y, r, n, rot, color, a) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r); g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  for (let i = 0; i < n; i++) { const a0 = i / n * 6.283, a1 = a0 + 6.283 / n * .45; ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, r, a0, a1); ctx.fill(); }
  ctx.restore();
}
function makeDust(n, color) { return { color, d: Array.from({ length: n }, () => ({ x: R(0, W), y: R(0, H), v: R(30, 90), r: R(1.5, 4), p: R(0, 6.28) })) }; }
function drawDust(D, t) {
  ctx.globalCompositeOperation = 'lighter';
  for (const d of D.d) {
    const y = ((d.y - t * d.v) % H + H) % H, x = d.x + Math.sin(t * 1.3 + d.p) * 18;
    ctx.fillStyle = D.color.replace('A', .4 + .4 * Math.sin(t * 4 + d.p)); ctx.beginPath(); ctx.arc(x, y, d.r, 0, 6.28); ctx.fill();
  }
  ctx.globalCompositeOperation = 'source-over';
}
function sparkle(x, y, size, rot, a) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = `rgba(255,250,210,${a})`;
  for (let r = 0; r < 4; r++) { ctx.rotate(Math.PI / 2); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(size * .15, 0); ctx.lineTo(0, size); ctx.lineTo(-size * .15, 0); ctx.fill(); }
  ctx.restore();
}

// ---------- text ----------
const tl = layer(), tlx = tl.getContext('2d');
function goldText(txt, x, y, font, size, alpha, shimmerU, opts = {}) {
  if (alpha <= 0) return;
  tlx.clearRect(0, 0, W, H);
  tlx.font = font.replace('$', size); tlx.textAlign = 'center'; tlx.textBaseline = 'alphabetic';
  const g = tlx.createLinearGradient(0, y - size * .85, 0, y + size * .15);
  g.addColorStop(0, '#fff7cf'); g.addColorStop(.35, '#ffd659'); g.addColorStop(.7, '#e39516'); g.addColorStop(1, '#ffe48c');
  if (opts.stroke) { tlx.lineWidth = opts.stroke; tlx.strokeStyle = opts.strokeColor || '#5a1e00'; tlx.lineJoin = 'round'; tlx.strokeText(txt, x, y + 4); }
  tlx.fillStyle = g; tlx.fillText(txt, x, y);
  if (shimmerU != null && shimmerU > 0 && shimmerU < 1) {
    tlx.globalCompositeOperation = 'source-atop';
    const sx = lerp(-300, W + 300, shimmerU), sg = tlx.createLinearGradient(sx - 140, 0, sx + 140, 0);
    sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(.5, 'rgba(255,255,255,.95)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
    tlx.fillStyle = sg; tlx.fillRect(0, 0, W, H); tlx.globalCompositeOperation = 'source-over';
  }
  ctx.save(); ctx.globalAlpha = alpha; ctx.shadowColor = opts.glow || 'rgba(255,140,20,.9)'; ctx.shadowBlur = opts.blur ?? 40;
  ctx.drawImage(tl, 0, 0); ctx.restore();
}
function plainText(txt, x, y, font, color, alpha, shadow = 'rgba(0,0,0,.7)') {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.font = font; ctx.textAlign = 'center'; ctx.fillStyle = color;
  ctx.shadowColor = shadow; ctx.shadowBlur = 16; ctx.fillText(txt, x, y); ctx.restore();
}

// ---------- logo ----------
const logos = {};
async function loadSvg(name, w, h) {
  const img = new Image(); img.src = '../logo/' + name; await img.decode();
  const c = document.createElement('canvas'); c.width = w; c.height = h; c.getContext('2d').drawImage(img, 0, 0, w, h); return c;
}
async function prepLogos() {
  logos.stacked = await loadSvg('unique-logo-stacked.svg', 1400, 1150);
  logos.horiz = await loadSvg('unique-logo-horizontal.svg', 1700, 540);
}
// small logo in the top-right corner
function cornerLogo(t, a, y = 40) {
  if (a <= 0) return;
  const w = 330, h = 118, x = W - w - 30;
  ctx.save(); ctx.globalAlpha = a;
  ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 6;
  ctx.fillStyle = 'rgba(255,252,242,.96)'; ctx.beginPath(); ctx.roundRect(x, y, w, h, 26); ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.strokeStyle = 'rgba(214,160,40,.9)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.roundRect(x + 6, y + 6, w - 12, h - 12, 21); ctx.stroke();
  ctx.drawImage(logos.horiz, x + 18, y + 13, w - 36, (w - 36) * 540 / 1700);
  ctx.restore();
}
// big logo card for the closing wishes
function endCard(t, t0, lines, cy = 800) {
  const ci = prog(t, t0, t0 + .9); if (ci <= 0) return;
  ctx.fillStyle = `rgba(15,3,20,${.45 * easeOutCubic(ci)})`; ctx.fillRect(0, 0, W, H);
  const sc = easeOutBack(ci), cx = W / 2, cw = 820, ch = 720;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc); ctx.rotate((1 - easeOutCubic(ci)) * -0.15);
  const pulse = .5 + .5 * Math.sin(t * 3);
  ctx.shadowColor = `rgba(255,190,60,${.8 + .2 * pulse})`; ctx.shadowBlur = 60 + 30 * pulse;
  ctx.fillStyle = '#fffaf0'; ctx.beginPath(); ctx.roundRect(-cw / 2, -ch / 2, cw, ch, 48); ctx.fill(); ctx.shadowBlur = 0;
  const bg = ctx.createLinearGradient(-cw / 2, -ch / 2, cw / 2, ch / 2);
  bg.addColorStop(0, '#fff0a0'); bg.addColorStop(.5, '#d99a1e'); bg.addColorStop(1, '#ffe17a');
  ctx.strokeStyle = bg; ctx.lineWidth = 12; ctx.beginPath(); ctx.roundRect(-cw / 2 + 14, -ch / 2 + 14, cw - 28, ch - 28, 38); ctx.stroke();
  ctx.drawImage(logos.stacked, -365, -315, 730, 600);
  const su = prog(t, t0 + .9, t0 + 1.8);
  if (su > 0 && su < 1) {
    ctx.save(); ctx.beginPath(); ctx.roundRect(-cw / 2, -ch / 2, cw, ch, 48); ctx.clip(); ctx.rotate(-0.4);
    const sx = lerp(-900, 900, su), sg = ctx.createLinearGradient(sx - 90, 0, sx + 90, 0);
    sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(.5, 'rgba(255,255,255,.75)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = sg; ctx.fillRect(-1200, -1200, 2400, 2400); ctx.restore();
  }
  ctx.restore();
  let y = cy + ch / 2 + 110;
  lines.forEach((L, i) => {
    const a = easeOutCubic(prog(t, t0 + 1 + i * .3, t0 + 1.7 + i * .3)), dy = (1 - a) * 30;
    if (L.gold) goldText(L.text, W / 2, y + dy, L.font, L.size, a, prog(t, t0 + 2.4, t0 + 3.4), { blur: 24 });
    else plainText(L.text, W / 2, y + dy, L.font, L.color, a);
    y += L.gap;
  });
}
const CONTACT = [
  { text: 'Vinod S. Patil & Team', font: '700 $px Pop', size: 62, gold: true, gap: 66 },
  { text: 'Unique Biological & Chemicals, Kolhapur', font: '600 36px Pop', color: '#ffffff', gap: 78 },
  { text: '☎  97302 83030   |   99222 80555', font: '600 40px Pop', color: '#ffd76a', gap: 0 },
];
function fadeEdges(t, dur) {
  const f = Math.max(1 - prog(t, 0, 0.6), prog(t, dur - 0.45, dur));
  if (f > 0) { ctx.fillStyle = `rgba(0,0,0,${f})`; ctx.fillRect(0, 0, W, H); }
}
async function loadFonts(extra = []) {
  await Promise.all([
    document.fonts.load('190px Vibes'), document.fonts.load('700 200px Cinzel'),
    document.fonts.load('100px Yatra', 'शुभ धनत्रयोदशी पाडवा लाभ श्री'), document.fonts.load('100px Yatra', 'abc'),
    document.fonts.load('500 40px Pop'), document.fonts.load('600 40px Pop'), document.fonts.load('700 40px Pop'), ...extra,
  ]);
}
