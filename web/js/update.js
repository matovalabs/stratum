// Update check for the Mac and Windows apps. On launch (and from Help) it asks the download site which alpha is newest and,
// when this build is older, offers a link to the download page. The web app on phones and browsers updates itself, so it
// never asks. Nothing is downloaded or installed here: the producer fetches the new version from the (Discord-gated) site.
(function () {
  const S = window.S, IO = S.io, U = S.ui;
  const LATEST = 'https://stratum-studio-pi.vercel.app/api/latest';
  const parts = (v) => String(v).split('.').map((x) => parseInt(x, 10) || 0);
  // True when alpha `a` is newer than alpha `b` ("11.10" is newer than "11.9").
  const newer = (a, b) => {
    const x = parts(a), y = parts(b);
    for (let i = 0; i < Math.max(x.length, y.length); i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d > 0; }
    return false;
  };
  async function latest() {
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 8000);
    try {
      const r = await fetch(LATEST, { cache: 'no-store', signal: ctl.signal });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json();
      if (!j || !/^[0-9]+(\.[0-9]+)*$/.test(String(j.alpha || ''))) throw new Error('no version in the answer');
      return { alpha: String(j.alpha), page: typeof j.page === 'string' && /^https:\/\//.test(j.page) ? j.page : LATEST.replace('/api/latest', '/#download') };
    } finally { clearTimeout(t); }
  }
  function bar(info) {
    let el = document.getElementById('updateBar');
    if (!el) { el = document.createElement('div'); el.id = 'updateBar'; document.body.appendChild(el); }
    el.innerHTML = `<span>STRATUM Alpha ${info.alpha} is out. You have ${S.ALPHA}.</span><button class="primary" data-act="updateGo">Get it</button><button data-act="updateLater">Not now</button>`;
    el.dataset.page = info.page; el.hidden = false;
  }
  // `ask`: the producer pressed "Check for updates", so say so even when there is nothing new or the check failed.
  async function check(ask) {
    if (!IO.host()) return ask && U.toast('The web version updates itself: reload the page.');
    try {
      const info = await latest();
      if (newer(info.alpha, S.ALPHA)) bar(info);
      else if (ask) U.toast(`STRATUM Alpha ${S.ALPHA} is the newest version.`);
      return info;
    } catch (e) { if (ask) U.toast('Could not check for updates: ' + (e.message || e), true); }
  }
  S.update = { check, newer };
  if (!IO.host()) return;
  // Not during the self-checks, and a few seconds after launch so it never competes with loading a project.
  setTimeout(async () => {
    try { if (IO.native() && ((await S.plug.ask({ op: 'prefsGet' })) || {}).testing) return; } catch (e) {}
    check(false);
  }, 6000);
})();
