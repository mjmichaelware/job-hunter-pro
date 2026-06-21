/* visuals/volumetric.js — always-on aurora living wallpaper on #halo-canvas.
   SYSTEM OVERRIDE: ignores prefers-reduced-data and prefers-reduced-motion.
   Reacts to pointer position and system activity via updateVolumetric(). */

let _volRAF = null;
let _volIntensity = 0.75;
let _volStarted = false;
let _volMx = 0.5, _volMy = 0.5;  // normalised pointer position

const _BLOBS = [
  { hue: '0,255,204',  x: 0.16, y: 0.14, r: 0.68, ox: 0.12, oy: 0.08, sx: 0.00021, sy: 0.00017 },
  { hue: '157,0,255',  x: 0.84, y: 0.82, r: 0.64, ox: 0.13, oy: 0.09, sx: 0.00018, sy: 0.00014 },
  { hue: '0,170,255',  x: 0.52, y: 0.30, r: 0.52, ox: 0.14, oy: 0.11, sx: 0.00025, sy: 0.00020 },
  { hue: '200,0,255',  x: 0.30, y: 0.74, r: 0.50, ox: 0.13, oy: 0.10, sx: 0.00023, sy: 0.00016 },
  { hue: '0,255,170',  x: 0.78, y: 0.20, r: 0.42, ox: 0.15, oy: 0.12, sx: 0.00030, sy: 0.00024 },
  { hue: '120,40,255', x: 0.20, y: 0.60, r: 0.44, ox: 0.14, oy: 0.11, sx: 0.00027, sy: 0.00019 },
];

const _PARTICLES = Array.from({ length: 80 }, function (_, i) {
  return {
    x: Math.random(), y: Math.random(),
    dx: (Math.random() - 0.5) * 0.00020,
    dy: (Math.random() - 0.5) * 0.00016,
    r: 0.9 + Math.random() * 2.2,
    hue: i % 3 === 0 ? '0,255,204' : i % 3 === 1 ? '157,0,255' : '120,200,255',
  };
});

function initVolumetric() {
  const canvas = document.getElementById('halo-canvas');
  if (!canvas || !canvas.getContext) return;
  // SYSTEM OVERRIDE: always animate — do not gate on prefers-reduced-data or
  // prefers-reduced-motion. The canvas is the living wallpaper per owner directive.
  const SPEED = 1;
  const ctx = canvas.getContext('2d');
  if (!ctx || _volStarted) return;
  _volStarted = true;
  // Pointer tracking — parallax effect on blobs
  document.addEventListener('mousemove', function (e) { _volMx = e.clientX / window.innerWidth; _volMy = e.clientY / window.innerHeight; }, { passive: true });
  document.addEventListener('touchmove', function (e) { if (e.touches[0]) { _volMx = e.touches[0].clientX / window.innerWidth; _volMy = e.touches[0].clientY / window.innerHeight; } }, { passive: true });

  let W = 0, H = 0;
  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize, { passive: true });

  function frame(rawTs) {
    const ts = rawTs * SPEED;
    const I = _volIntensity;
    ctx.clearRect(0, 0, W, H);

    // Aurora nebula blobs — pointer position adds gentle parallax
    ctx.globalCompositeOperation = 'lighter';
    _BLOBS.forEach(function (b, i) {
      const px = (b.x + Math.sin(ts * b.sx + i * 1.3) * b.ox + (_volMx - 0.5) * 0.06 * (i % 2 ? 1 : -1)) * W;
      const py = (b.y + Math.cos(ts * b.sy + i * 1.9) * b.oy + (_volMy - 0.5) * 0.06 * (i % 3 ? 1 : -1)) * H;
      const rad = b.r * Math.min(W, H) * (0.90 + I * 0.4);
      const g = ctx.createRadialGradient(px, py, 0, px, py, rad);
      const a = (0.18 + I * 0.26).toFixed(3);
      g.addColorStop(0,    'rgba(' + b.hue + ',' + a + ')');
      g.addColorStop(0.45, 'rgba(' + b.hue + ',' + (0.07 + I * 0.12).toFixed(3) + ')');
      g.addColorStop(1,    'rgba(' + b.hue + ',0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, rad, 0, Math.PI * 2); ctx.fill();
    });

    // Flowing aurora wave band
    const bandY = H * (0.5 + Math.sin(ts * 0.00012) * 0.18);
    const wg = ctx.createLinearGradient(0, bandY - H * 0.3, 0, bandY + H * 0.3);
    wg.addColorStop(0,   'rgba(0,255,204,0)');
    wg.addColorStop(0.5, 'rgba(0,220,255,' + (0.06 + I * 0.09).toFixed(3) + ')');
    wg.addColorStop(1,   'rgba(157,0,255,0)');
    ctx.fillStyle = wg;
    ctx.fillRect(0, 0, W, H);

    // Constellation particles — drift + link nearby ones
    const pts = _PARTICLES.map(function (p) {
      p.x += p.dx; p.y += p.dy;
      if (p.x < -0.03) p.x = 1.03; if (p.x > 1.03) p.x = -0.03;
      if (p.y < -0.03) p.y = 1.03; if (p.y > 1.03) p.y = -0.03;
      return { sx: p.x * W, sy: p.y * H, r: p.r, hue: p.hue };
    });
    pts.forEach(function (p) {
      const a = (0.40 + I * 0.45).toFixed(3);
      const g = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, p.r * 4);
      g.addColorStop(0, 'rgba(' + p.hue + ',' + a + ')');
      g.addColorStop(1, 'rgba(' + p.hue + ',0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(p.sx, p.sy, p.r * 4, 0, Math.PI * 2); ctx.fill();
    });
    const linkDist = 130 + I * 60;
    ctx.lineWidth = 0.7;
    for (var a = 0; a < pts.length; a++) {
      for (var b = a + 1; b < pts.length; b++) {
        const dx = pts[a].sx - pts[b].sx, dy = pts[a].sy - pts[b].sy;
        const d = Math.hypot(dx, dy);
        if (d < linkDist) {
          ctx.strokeStyle = 'rgba(0,255,204,' + ((1 - d / linkDist) * (0.07 + I * 0.12)).toFixed(3) + ')';
          ctx.beginPath(); ctx.moveTo(pts[a].sx, pts[a].sy); ctx.lineTo(pts[b].sx, pts[b].sy); ctx.stroke();
        }
      }
    }

    ctx.globalCompositeOperation = 'source-over';
    _volRAF = window.requestAnimationFrame(frame);
  }
  _volRAF = window.requestAnimationFrame(frame);
}

function updateVolumetric(signal) {
  if (signal && typeof signal.intensity === 'number') {
    _volIntensity = Math.max(0.35, Math.min(1, signal.intensity));
  }
}
