/* components/boot_sequence.js — multi-phase ~5s launch splash (once per session).
   Phase A: stroke draw (0–1.3s). Phase B: halo + orbit bloom (0.6–2.8s).
   Phase C: name letter reveal (1.8–3.3s). Phase D: tagline fade (3.4s).
   Phase E: graceful fade-out (~4.6s). replayBootSequence() for replay. */

function _bootIsReduced() {
  return (typeof A11y !== 'undefined' && A11y.prefersReducedMotion && A11y.prefersReducedMotion())
    || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function _buildBootDOM(splash) {
  // Wrap the SVG in orbital container, inject orbital rings + dots, tagline
  var mark = splash.querySelector('#boot-mark');
  if (!mark) return;
  // Build orbital wrapper if not already done
  if (splash.querySelector('.boot-splash__orbital')) return;
  var wrapper = document.createElement('div');
  wrapper.className = 'boot-splash__orbital';
  wrapper.setAttribute('aria-hidden', 'true');
  // Orbital SVG rings + dots
  wrapper.innerHTML = '<div class="boot-orbit boot-orbit--1" aria-hidden="true"></div>'
    + '<div class="boot-orbit boot-orbit--2" aria-hidden="true"></div>'
    + '<div class="boot-dot boot-dot--a" aria-hidden="true"></div>'
    + '<div class="boot-dot boot-dot--b" aria-hidden="true"></div>'
    + '<div class="boot-dot boot-dot--c" aria-hidden="true"></div>';
  mark.parentNode.insertBefore(wrapper, mark);
  wrapper.appendChild(mark);
  // Phase C: split name into .boot-letter spans
  var nameEl = splash.querySelector('.boot-splash__name');
  if (nameEl && !nameEl.querySelector('.boot-letter')) {
    var text = nameEl.textContent.trim();
    nameEl.textContent = '';
    var baseDelay = 1.8;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (ch === ' ') { var sp = document.createTextNode(' '); nameEl.appendChild(sp); continue; }
      var span = document.createElement('span');
      span.className = 'boot-letter';
      span.textContent = ch;
      span.style.animationDelay = (baseDelay + i * 0.07) + 's';
      nameEl.appendChild(span);
    }
  }
  // Phase D: tagline element
  if (!splash.querySelector('.boot-splash__tagline')) {
    var tag = document.createElement('p');
    tag.className = 'boot-splash__tagline';
    tag.setAttribute('aria-hidden', 'true');
    tag.textContent = 'AI-Powered Local Opportunity Intelligence';
    nameEl.insertAdjacentElement('afterend', tag);
  }
}

function runBootSequence(done) {
  var splash = document.getElementById('boot-splash');
  var finish = function () { if (typeof done === 'function') done(); };
  var seen = false;
  try { seen = sessionStorage.getItem('jhp_booted') === '1'; } catch (e) {}
  if (!splash || seen) { finish(); return; }
  try { sessionStorage.setItem('jhp_booted', '1'); } catch (e) {}
  _runSplash(splash, finish);
}

function _runSplash(splash, finish) {
  splash.hidden = false;
  splash.setAttribute('aria-hidden', 'false');
  splash.classList.remove('is-leaving');
  var reduced = _bootIsReduced();
  if (!reduced) _buildBootDOM(splash);
  // Reduced-motion path: brief hold then out
  var hold = reduced ? 200 : 4600;
  var outDur = reduced ? 160 : 600;
  window.setTimeout(function () {
    splash.classList.add('is-leaving');
    window.setTimeout(function () {
      splash.hidden = true;
      splash.setAttribute('aria-hidden', 'true');
      if (typeof finish === 'function') finish();
    }, outDur);
  }, hold);
}

/* Clears session flags and re-runs the boot splash.
   navigate('landing') is called by title_replay.js after boot completes. */
function replayBootSequence(done) {
  try { sessionStorage.removeItem('jhp_booted'); } catch (e) {}
  try { sessionStorage.removeItem('jhp_entered'); } catch (e) {}
  var splash = document.getElementById('boot-splash');
  if (!splash) { if (typeof done === 'function') done(); return; }
  _runSplash(splash, done);
}
