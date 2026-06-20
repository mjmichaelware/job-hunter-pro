/* components/title_replay.js — clicking #app-title replays the boot splash,
   then navigates to the landing view. Wired after boot_sequence.js. */

(function () {
  function wireTitle() {
    var btn = document.getElementById('app-title');
    if (!btn) return;
    btn.addEventListener('click', function () {
      // replayBootSequence is defined in boot_sequence.js (loaded before this)
      if (typeof replayBootSequence === 'function') {
        replayBootSequence(function () {
          if (typeof navigate === 'function') navigate('landing');
        });
      } else {
        if (typeof navigate === 'function') navigate('landing');
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireTitle);
  } else {
    wireTitle();
  }
}());
