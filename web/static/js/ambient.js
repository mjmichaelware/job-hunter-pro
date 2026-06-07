(function initAmbientLayer() {
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (saveData || reducedMotion) return;

  const canvas = document.getElementById('ambient-canvas');
  if (!canvas || !canvas.getContext) return;

  const ctx = canvas.getContext('2d');
  let width = 0;
  let height = 0;
  let frame = 0;

  const seeds = Array.from({ length: 28 }, (_, index) => ({
    index,
    xRatio: ((index * 37) % 100) / 100,
    yRatio: ((index * 53) % 100) / 100,
    size: 0.75 + ((index * 7) % 5) * 0.28,
    phase: index * 0.41,
    drift: 0.12 + ((index * 11) % 9) * 0.01
  }));

  function resize() {
    width = canvas.width = window.innerWidth || 1;
    height = canvas.height = window.innerHeight || 1;
  }

  function draw() {
    frame += 1;
    ctx.clearRect(0, 0, width, height);

    seeds.forEach((seed) => {
      const x = seed.xRatio * width + Math.sin(frame * 0.006 + seed.phase) * 8;
      const y = seed.yRatio * height + Math.cos(frame * 0.004 + seed.phase) * 8;
      const alpha = 0.05 + ((seed.index % 6) * 0.012);

      ctx.beginPath();
      ctx.arc(x, y, seed.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(187, 134, 252, ${alpha})`;
      ctx.fill();
    });

    window.requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener('resize', resize, { passive: true });
  window.requestAnimationFrame(draw);
})();
