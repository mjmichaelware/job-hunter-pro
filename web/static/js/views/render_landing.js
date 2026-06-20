/* views/render_landing.js — entry landing page. Centered brand + Enter button.
   Hidden from the nav rail; routable at #landing. Enter → Home. No network.
   Kinetic entrance animations on title/tag; glowing floating Enter button. */

function loadLandingView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<section class="landing">'
    + '<svg class="landing__mark kinetic-in" viewBox="0 0 120 120" width="96" height="96" aria-hidden="true">'
    + '<circle cx="60" cy="60" r="44" fill="none" stroke="var(--c-cyan)" stroke-width="2" opacity="0.4"/>'
    + '<path d="M78 26 L78 78 a22 22 0 1 1 -22 -22" fill="none" stroke="var(--c-text)" stroke-width="6" stroke-linecap="round"/>'
    + '</svg>'
    + '<h1 class="landing__title kinetic-in" style="--ki-delay:0.08s">'
    + '<span class="kinetic-in" style="--ki-delay:0.10s">Job Hunter Pro</span></h1>'
    + '<p class="landing__tag kinetic-in" style="--ki-delay:0.22s">' + esc(t('landing.tag')) + '</p>'
    + '<button type="button" id="landing-enter" class="btn btn-enter btn-enter--glow kinetic-in" style="--ki-delay:0.36s">'
    + esc(t('landing.enter')) + '</button>'
    + '<p class="landing__note kinetic-in" style="--ki-delay:0.48s">' + esc(t('landing.safe')) + '</p>'
    + '</section>';
  const enter = el.querySelector('#landing-enter');
  if (enter) enter.addEventListener('click', function () {
    try { sessionStorage.setItem('jhp_entered', '1'); } catch (e) {}
    navigate('home');
  });
}

registerView('landing', 'Landing', loadLandingView, { hidden: true });
