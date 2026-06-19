/* visuals/volumetric.js — ambient Probability Halo field on #halo-canvas.
   Canvas-2D (universally supported); the CSS gradient in shaders.css is the
   no-JS fallback. Calm by default; intensity can be modulated by a REAL signal
   via updateVolumetric({intensity}) — never animated to imply activity that
   isn't happening. Disabled entirely under prefers-reduced-motion. */

let _volRAF = null;
let _volIntensity = 0.5; // 0..1, default calm

function initVolumetric() {
  const canvas = document.getElementById('halo-canvas');
  if (!canvas || !canvas.getContext) return;
  if (A11y.prefersReducedMotion()) return; // CSS fallback / nothing
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  const blobs = [
    { hue: '0,255,204', x: 0.2, y: 0.15, r: 0.45, dx: 0.00006, dy: 0.00004 },
    { hue: '157,0,255', x: 0.82, y: 0.85, r: 0.4, dx: -0.00005, dy: -0.00003 },
  ];

  function frame(ts) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = 'lighter';
    const W = canvas.width, H = canvas.height;
    blobs.forEach(function (b, i) {
      const px = (b.x + Math.sin(ts * b.dx + i) * 0.04) * W;
      const py = (b.y + Math.cos(ts * b.dy + i) * 0.04) * H;
      const rad = b.r * Math.min(W, H);
      const g = ctx.createRadialGradient(px, py, 0, px, py, rad);
      const a = 0.10 + _volIntensity * 0.12;
      g.addColorStop(0, 'rgba(' + b.hue + ',' + a.toFixed(3) + ')');
      g.addColorStop(1, 'rgba(' + b.hue + ',0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, rad, 0, Math.PI * 2); ctx.fill();
    });
    _volRAF = window.requestAnimationFrame(frame);
  }
  _volRAF = window.requestAnimationFrame(frame);
}

// Modulate the field from a real, computed signal (e.g., budget remaining 0..1).
function updateVolumetric(signal) {
  if (signal && typeof signal.intensity === 'number') {
    _volIntensity = Math.max(0, Math.min(1, signal.intensity));
  }
}
