/* visuals/volumetric.js — ambient volumetric halo field on #halo-canvas.
   6-blob nebula + particle field driven by real system state via updateVolumetric().
   Disabled entirely under prefers-reduced-motion. */

let _volRAF = null;
let _volIntensity = 0.5;
let _volStarted = false;

const _BLOBS = [
  { hue: '0,255,204',   x: 0.15, y: 0.12, r: 0.55, dx: 0.000038, dy: 0.000026 },
  { hue: '157,0,255',   x: 0.85, y: 0.80, r: 0.50, dx: -0.000034, dy: -0.000020 },
  { hue: '0,180,255',   x: 0.52, y: 0.28, r: 0.42, dx: 0.000022, dy: -0.000032 },
  { hue: '200,0,255',   x: 0.28, y: 0.72, r: 0.44, dx: -0.000028, dy: 0.000016 },
  { hue: '0,255,180',   x: 0.78, y: 0.18, r: 0.34, dx: 0.000048, dy: 0.000038 },
  { hue: '80,0,255',    x: 0.18, y: 0.62, r: 0.36, dx: -0.000044, dy: -0.000030 },
];

const _PARTICLES = Array.from({ length: 60 }, (_, i) => ({
  x: Math.random(), y: Math.random(),
  r: 0.6 + Math.random() * 1.8,
  dx: (Math.random() - 0.5) * 0.00012,
  dy: (Math.random() - 0.5) * 0.00010,
  alpha: 0.15 + Math.random() * 0.55,
  hue: i % 3 === 0 ? '0,255,204' : i % 3 === 1 ? '157,0,255' : '0,200,255',
}));

function initVolumetric() {
  const canvas = document.getElementById('halo-canvas');
  if (!canvas || !canvas.getContext) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  if (_volStarted) return;
  _volStarted = true;

  function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize, { passive: true });

  function frame(ts) {
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Nebula blobs
    ctx.globalCompositeOperation = 'lighter';
    _BLOBS.forEach(function (b, i) {
      const px = (b.x + Math.sin(ts * b.dx + i * 1.4) * 0.055) * W;
      const py = (b.y + Math.cos(ts * b.dy + i * 1.7) * 0.055) * H;
      const rad = b.r * Math.min(W, H) * (0.8 + _volIntensity * 0.4);
      const g = ctx.createRadialGradient(px, py, 0, px, py, rad);
      const a = (0.09 + _volIntensity * 0.16).toFixed(3);
      const a2 = (0.04 + _volIntensity * 0.08).toFixed(3);
      g.addColorStop(0,   'rgba(' + b.hue + ',' + a + ')');
      g.addColorStop(0.4, 'rgba(' + b.hue + ',' + a2 + ')');
      g.addColorStop(1,   'rgba(' + b.hue + ',0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, rad, 0, Math.PI * 2); ctx.fill();
    });

    // Particle field
    ctx.globalCompositeOperation = 'lighter';
    _PARTICLES.forEach(function (p) {
      p.x += p.dx; p.y += p.dy;
      if (p.x < -0.02) p.x = 1.02;
      if (p.x > 1.02)  p.x = -0.02;
      if (p.y < -0.02) p.y = 1.02;
      if (p.y > 1.02)  p.y = -0.02;
      const px = p.x * W, py = p.y * H;
      const a = (p.alpha * (0.5 + _volIntensity * 0.6)).toFixed(3);
      const g = ctx.createRadialGradient(px, py, 0, px, py, p.r * 4);
      g.addColorStop(0, 'rgba(' + p.hue + ',' + a + ')');
      g.addColorStop(1, 'rgba(' + p.hue + ',0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, p.r * 4, 0, Math.PI * 2); ctx.fill();
    });

    // Subtle grid pulse (only at medium-high intensity)
    if (_volIntensity > 0.3) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = 'rgba(0,255,204,' + ((_volIntensity - 0.3) * 0.025).toFixed(3) + ')';
      ctx.lineWidth = 0.5;
      const step = Math.max(80, 160 - _volIntensity * 80);
      for (let x = 0; x < W; x += step) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += step) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }
    }

    ctx.globalCompositeOperation = 'source-over';
    _volRAF = window.requestAnimationFrame(frame);
  }
  _volRAF = window.requestAnimationFrame(frame);
}

function updateVolumetric(signal) {
  if (signal && typeof signal.intensity === 'number') {
    _volIntensity = Math.max(0, Math.min(1, signal.intensity));
  }
}
