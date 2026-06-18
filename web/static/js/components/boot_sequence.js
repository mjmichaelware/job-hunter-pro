/* components/boot_sequence.js — play the launch splash once per session, then
   reveal the app. Respects prefers-reduced-motion (instant fade). No data, no
   network — pure presentation. Router calls runBootSequence() during boot. */

function runBootSequence(done) {
  const splash = document.getElementById('boot-splash');
  const finish = function () { if (typeof done === 'function') done(); };

  // Already shown this session, or no splash element → skip straight to app.
  let seen = false;
  try { seen = sessionStorage.getItem('jhp_booted') === '1'; } catch (e) {}
  if (!splash || seen) { finish(); return; }

  try { sessionStorage.setItem('jhp_booted', '1'); } catch (e) {}

  splash.hidden = false;
  splash.setAttribute('aria-hidden', 'false');

  const reduced = (typeof A11y !== 'undefined' && A11y.prefersReducedMotion && A11y.prefersReducedMotion());
  const hold = reduced ? 200 : 1900;   // let the draw/bloom play, then leave

  window.setTimeout(function () {
    splash.classList.add('is-leaving');
    window.setTimeout(function () {
      splash.hidden = true;
      splash.setAttribute('aria-hidden', 'true');
      finish();
    }, reduced ? 160 : 520);
  }, hold);
}
