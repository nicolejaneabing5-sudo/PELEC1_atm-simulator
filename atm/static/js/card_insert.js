(function () {
  var SOUND_ON = false;   // set to false to turn all sound effects off

  var root = document.getElementById('abcCardInsert');
  if (!root) return;
  var pin = document.querySelector(root.getAttribute('data-pin'));
  if (!pin) { console.warn('card_insert: PIN wrapper not found'); root.remove(); return; }

  root.style.minHeight = pin.offsetHeight + 'px';   // keep the panel height steady
  pin.style.display = 'none';

  var $ = function (id) { return document.getElementById(id); };
  var card = $('abcCiCard'), chip = $('abcCiChip'), led = $('abcCiLed'), slot = $('abcCiSlot'),
      btn = $('abcCiBtn'), btnText = $('abcCiBtnText'), status = $('abcCiStatus'),
      hint = status.textContent, THRESHOLD = 70, started = false, dragging = false, y0 = 0, dy = 0,
      fast = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var wait = function (ms) { return new Promise(function (r) { setTimeout(r, fast ? 120 : ms); }); };
  var maxDy = function () { return card.offsetHeight + 50; };

  /* ---------- sound effects (synthesized, no files needed) ---------- */
  var AC = window.AudioContext || window.webkitAudioContext, ctx = null;

  function audio() {
    if (!AC) return null;    try {
      if (!ctx) ctx = new AC();
      if (ctx.state === 'suspended') ctx.resume();
    } catch (e) { return null; }
    return ctx;
  }

  function tone(freq, delay, dur, vol, endFreq) {
    var c = audio(); if (!c) return;
    var t = c.currentTime + delay, o = c.createOscillator(), g = c.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (endFreq) o.frequency.exponentialRampToValueAtTime(endFreq, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(c.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }

  function playSlide(sec) {                       // card swiping through the reader
    var c = audio(); if (!c) return;
    var t = c.currentTime, len = Math.max(1, Math.floor(c.sampleRate * sec));
    var buf = c.createBuffer(1, len, c.sampleRate), d = buf.getChannelData(0);
    for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    var src = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain();
    src.buffer = buf;
    f.type = 'bandpass'; f.Q.value = 1.1;
    f.frequency.setValueAtTime(900, t);
    f.frequency.exponentialRampToValueAtTime(2800, t + sec);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.16, t + 0.06);
    g.gain.exponentialRampToValueAtTime(0.0001, t + sec);
    src.connect(f); f.connect(g); g.connect(c.destination);
    src.start(t);
  }

  function playThunk() { tone(140, 0, 0.14, 0.4, 55); }                       // card seats in the reader
  function playBeep() { tone(1400, 0, 0.12, 0.18); tone(1850, 0.15, 0.2, 0.18); }   // card accepted

  /* ---------- card movement ---------- */
  function moveCard(px, ms) {
    card.style.transition = ms ? 'transform ' + ms + 'ms cubic-bezier(.4,0,.2,1)' : 'none';
    card.style.transform = 'translateY(' + (-px) + 'px)';
  }

  async function insert(ms) {
    if (started) return;
    started = true; root.classList.add('is-started');
    audio();                                      // unlock sound inside the user's click/swipe
    var dur = fast ? 100 : ms;
    btn.disabled = true; btnText.textContent = 'Inserting\u2026'; status.textContent = 'Inserting card\u2026';
    led.classList.add('is-busy'); slot.classList.add('is-scan'); chip.classList.add('is-reading');
    playSlide(dur / 1000);
    moveCard(maxDy(), dur);
    await wait(ms + 150);
    playThunk();
    btnText.textContent = 'Reading card\u2026'; status.textContent = 'Reading chip\u2026'; await wait(1000);
    chip.classList.remove('is-reading'); slot.classList.remove('is-scan');
    led.classList.remove('is-busy'); led.classList.add('is-ok');
    btnText.textContent = 'Card accepted'; status.textContent = 'Card accepted. Enter your PIN.';
    playBeep();
    await wait(650);
    root.classList.add('is-leaving'); await wait(380);
    window.removeEventListener('keydown', trap, true);
    root.remove(); pin.style.display = ''; pin.classList.add('abc-ci-in');
    var f = pin.querySelector('input:not([type=hidden])'); if (f) f.focus({ preventScroll: true });
    document.dispatchEvent(new CustomEvent('atm:card-inserted'));
  }

  // keep keystrokes away from the PIN keypad until the card is in
  function trap(e) { if (e.key === 'Tab') return; e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); insert(1200); } }
  window.addEventListener('keydown', trap, true);
  btn.addEventListener('click', function () { insert(1200); });
  btn.focus({ preventScroll: true });

  // the user swipes the card up into the slot
  card.addEventListener('pointerdown', function (e) {
    if (started) return;
    audio();
    dragging = true; y0 = e.clientY; dy = 0;
    card.setPointerCapture(e.pointerId);
  });
  card.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    dy = Math.max(0, Math.min(y0 - e.clientY, maxDy()));
    moveCard(dy, 0);
    slot.classList.toggle('is-scan', dy > 12);
    status.textContent = dy >= THRESHOLD ? 'Release to insert' : 'Keep swiping up\u2026';
  });
  function release() {
    if (!dragging) return;
    dragging = false;
    if (dy >= THRESHOLD) { insert(600); }
    else { moveCard(0, 300); slot.classList.remove('is-scan'); status.textContent = hint; }
  }
  card.addEventListener('pointerup', release);
  card.addEventListener('pointercancel', release);
})();

(function () {
  var SOUND_ON = true;

  var trigger = document.querySelector('[data-lock-session]');
  if (!trigger) return;

  var last4 = trigger.getAttribute('data-last4') || '4821',
      expiry = trigger.getAttribute('data-expiry') || '09/29',
      name = (trigger.getAttribute('data-name') || 'JUAN DELA CRUZ').toUpperCase(),
      running = false,
      fast = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var wait = function (ms) { return new Promise(function (r) { setTimeout(r, fast ? 120 : ms); }); };

  var AC = window.AudioContext || window.webkitAudioContext, ctx = null;
  function audio() {
    if (!SOUND_ON || !AC) return null;
    try { if (!ctx) ctx = new AC(); if (ctx.state === 'suspended') ctx.resume(); } catch (e) { return null; }
    return ctx;
  }
  function tone(freq, delay, dur, vol, endFreq) {
    var c = audio(); if (!c) return;
    var t = c.currentTime + delay, o = c.createOscillator(), g = c.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (endFreq) o.frequency.exponentialRampToValueAtTime(endFreq, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(c.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }
  function playSlide(sec) {
    var c = audio(); if (!c) return;
    var t = c.currentTime, len = Math.max(1, Math.floor(c.sampleRate * sec));
    var buf = c.createBuffer(1, len, c.sampleRate), d = buf.getChannelData(0);
    for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    var src = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain();
    src.buffer = buf; f.type = 'bandpass'; f.Q.value = 1.1;
    f.frequency.setValueAtTime(2800, t);
    f.frequency.exponentialRampToValueAtTime(900, t + sec);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.16, t + 0.06);
    g.gain.exponentialRampToValueAtTime(0.0001, t + sec);
    src.connect(f); f.connect(g); g.connect(c.destination);
    src.start(t);
  }
  function playThunk() { tone(140, 0, 0.14, 0.4, 55); }
  function playBeep() { tone(1850, 0, 0.12, 0.18); tone(1400, 0.15, 0.2, 0.18); }

  function build() {
    var el = document.createElement('div');
    el.className = 'abc-eject';
    el.innerHTML =
      '<div class="abc-eject__panel"><div class="abc-ci">' +
        '<header class="abc-ci__header"><div>' +
          '<p class="abc-ci__eyebrow">SESSION LOCKED</p>' +
          '<h2 class="abc-ci__title">Take your card</h2></div>' +
          '<div class="abc-ci__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3 10h18M7 15h4"/></svg></div>' +
        '</header>' +
        '<p class="abc-ci__desc">Your session is locked. Your card is being returned.</p>' +
        '<div class="abc-ci__reader">' +
          '<div class="abc-ci__slot"><i></i><span class="abc-ci__led"></span></div>' +
          '<div class="abc-ci__bay"><div class="abc-ci__float">' +
            '<div class="abc-ci__card">' +
              '<div class="abc-ci__brand">ABC CARD</div>' +
              '<div class="abc-ci__chip"><i></i><i></i><i></i></div>' +
              '<div class="abc-ci__num">&bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; ' + last4 + '</div>' +
              '<div class="abc-ci__last4">' + last4 + '</div>' +
              '<div class="abc-ci__valid"><small>VALID<br>THRU</small><span>' + expiry + '</span></div>' +
              '<div class="abc-ci__name">' + name + '</div>' +
              '<div class="abc-ci__logo"><span class="abc-ci__dot abc-ci__dot--r"></span><span class="abc-ci__dot abc-ci__dot--o"></span><em>ABC</em></div>' +
              '<i class="abc-ci__edge"></i>' +
            '</div></div></div>' +
        '</div>' +
        '<p class="abc-ci__note" role="status" aria-live="polite">Ejecting card\u2026</p>' +
      '</div></div>';
    return el;
  }

  function move(card, px, ms) {
    card.style.transition = ms ? 'transform ' + ms + 'ms cubic-bezier(.4,0,.2,1)' : 'none';
    card.style.transform = 'translateY(' + (-px) + 'px)';
  }

  function leave() {
    var form = trigger.closest('form');
    if (trigger.tagName === 'A' && trigger.href) { window.location.href = trigger.href; }
    else if (form) { form.submit(); }
    else if (trigger.getAttribute('data-href')) { window.location.href = trigger.getAttribute('data-href'); }
  }

  async function eject(e) {
    e.preventDefault();
    if (running) return;
    running = true;
    audio();

    var overlay = build();
    document.body.appendChild(overlay);
    var card = overlay.querySelector('.abc-ci__card'),
        led = overlay.querySelector('.abc-ci__led'),
        slot = overlay.querySelector('.abc-ci__slot'),
        status = overlay.querySelector('.abc-ci__note');

    move(card, card.offsetHeight + 50, 0);   // start fully inside the reader
    void card.offsetHeight;

    led.classList.add('is-busy'); slot.classList.add('is-scan');
    await wait(500);
    playThunk();
    await wait(250);

    var dur = fast ? 100 : 1200;
    playSlide(dur / 1000);
    move(card, 0, dur);                      // slide OUT
    await wait(dur + 150);

    slot.classList.remove('is-scan');
    led.classList.remove('is-busy'); led.classList.add('is-ok');
    status.textContent = 'Card ejected. Please take your card.';
    playBeep();
    await wait(1200);

    overlay.style.transition = 'opacity .35s ease';
    overlay.style.opacity = '0';
    await wait(380);
    leave();
  }

  trigger.addEventListener('click', eject);
})();