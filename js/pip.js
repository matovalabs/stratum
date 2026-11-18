// Camera layouts for Go live and share videos: where the producer's camera goes and where the beat (the STRATUM window,
// the waveform or the Visuals) goes. The same layout drives the preview here, the share video drawn in the page, and the
// Mac and Windows live compositors (which get the result as rectangles, as fractions of the frame).
(function () {
  const S = window.S, P = (S.pip = {});
  P.MODES = [
    ['none', 'No camera'],
    ['box', 'Camera box (drag it)'],
    ['above', 'Camera above'],
    ['beside', 'Side by side'],
    ['big', 'Camera big, beat in a box (drag it)'],
  ];
  // Shares start without the camera; Go live starts with it beside the window, as it always did.
  const DEFAULT = { mode: 'none', x: 0.82, y: 0.8, s: 0.28, mic: false };
  const load = () => { try { return JSON.parse(localStorage.getItem('stratum.pip') || '{}'); } catch (e) { return {}; } };
  const save = (all) => { try { localStorage.setItem('stratum.pip', JSON.stringify(all)); } catch (e) {} };
  // `use` is 'live' or 'share'; each remembers its own layout.
  P.get = (use) => ({ ...DEFAULT, ...(use === 'live' ? { mode: 'beside', s: 0.22 } : {}), ...(load()[use] || {}) });
  P.set = (use, v) => { const all = load(); all[use] = { ...P.get(use), ...v }; save(all); };
  P.camera = (lay) => lay.mode !== 'none';

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  // Rectangles [x, y, w, h] as fractions of a W x H frame. camTop: the camera is drawn over the beat (otherwise the beat is
  // drawn over the camera). The beat is fitted inside its rectangle; the camera fills its rectangle, cropped.
  P.rects = (lay, W, H) => {
    const port = H > W, m = 0.025, camAR = port ? 4 / 5 : 16 / 9;
    const place = (wFrac, ar) => {
      const w = clamp(wFrac, 0.12, 0.7), h = (w * W) / ar / H;
      return [clamp(lay.x - w / 2, m, 1 - m - w), clamp(lay.y - h / 2, m, 1 - m - h), w, h];
    };
    switch (lay.mode) {
      case 'box': return { main: [0, 0, 1, 1], cam: place(lay.s, camAR), camTop: true };
      case 'big': return { main: place(lay.s * 1.3, W / H), cam: [0, 0, 1, 1], camTop: false };
      case 'above': {
        if (port) return { main: [0, 0.42, 1, 0.58], cam: [0, 0, 1, 0.42], camTop: true };
        const h = 0.42, w = (h * H * 16) / 9 / W;
        return { main: [0, h + 0.02, 1, 1 - h - 0.02], cam: [(1 - w) / 2, 0.01, w, h], camTop: true };
      }
      case 'beside': {
        if (port) return { main: [0, 0, 1, 0.6], cam: [0.05, 0.62, 0.9, 0.36], camTop: true };
        const cw = 0.24, ch = (cw * W * 9) / 16 / H, pad = 12 / W;
        return { main: [pad, 0, 1 - cw - pad * 3, 1], cam: [1 - cw - pad, 1 - ch - 0.03, cw, ch], camTop: true };
      }
      default: return { main: [0, 0, 1, 1], cam: null, camTop: true };
    }
  };

  // Drawing helpers shared by the preview and the share renderer.
  const px = (r, W, H) => [r[0] * W, r[1] * H, r[2] * W, r[3] * H];
  P.drawFit = (g, src, sw, sh, r, bg) => {
    const [x, y, w, h] = r, s = Math.min(w / sw, h / sh), dw = sw * s, dh = sh * s;
    if (bg) { g.fillStyle = bg; g.fillRect(x, y, w, h); }
    g.drawImage(src, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
  };
  P.drawCover = (g, src, sw, sh, r, mirror) => {
    const [x, y, w, h] = r, s = Math.max(w / sw, h / sh), cw = w / s, ch = h / s;
    g.save(); g.beginPath(); g.rect(x, y, w, h); g.clip();
    if (mirror) { g.translate(x + w, y); g.scale(-1, 1); g.drawImage(src, (sw - cw) / 2, (sh - ch) / 2, cw, ch, 0, 0, w, h); }
    else g.drawImage(src, (sw - cw) / 2, (sh - ch) / 2, cw, ch, x, y, w, h);
    g.restore();
  };
  P.frameBox = (g, r, color, k) => { g.save(); g.strokeStyle = color; g.lineWidth = Math.max(2, 4 * k); g.strokeRect(r[0], r[1], r[2], r[3]); g.restore(); };
  // Composes one frame: `drawMain(g, x, y, w, h)` paints the beat into its rectangle; the camera comes from a <video>.
  P.compose = (g, W, H, lay, drawMain, video, opt = {}) => {
    const R = P.rects(lay, W, H), main = px(R.main, W, H), cam = R.cam && px(R.cam, W, H), k = Math.min(W, H) / 1080;
    g.fillStyle = opt.bg || '#0f1016'; g.fillRect(0, 0, W, H);
    const drawCam = () => {
      if (!cam) return;
      const vw = video && (video.videoWidth || video.width), vh = video && (video.videoHeight || video.height);
      if (vw && vh) P.drawCover(g, video, vw, vh, cam, true);
      else { g.fillStyle = '#262a38'; g.fillRect(cam[0], cam[1], cam[2], cam[3]); g.fillStyle = '#8f8d88'; g.font = `600 ${Math.max(11, cam[3] * 0.12)}px -apple-system, "Segoe UI", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('Camera', cam[0] + cam[2] / 2, cam[1] + cam[3] / 2); }
    };
    const accent = opt.accent || '#e39a12';
    if (R.camTop) { drawMain(g, ...main); drawCam(); if (cam && lay.mode !== 'above') P.frameBox(g, cam, accent, k); }
    else { drawCam(); drawMain(g, ...main); P.frameBox(g, main, accent, k); }
    return R;
  };

  // ---------------------------------------------------------------- the camera
  let stream = null, videoEl = null, users = 0;
  P.openCamera = async (withMic) => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('This app version cannot use the camera here.');
    if (stream && (!withMic || stream.getAudioTracks().length)) { users++; return { video: videoEl, stream }; }
    P.closeCamera(true);
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: withMic ? { echoCancellation: true, noiseSuppression: true } : false });
    videoEl = document.createElement('video'); videoEl.muted = true; videoEl.playsInline = true; videoEl.srcObject = stream;
    await videoEl.play().catch(() => {});
    users = 1;
    return { video: videoEl, stream };
  };
  P.closeCamera = (force) => {
    if (!force && --users > 0) return;
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = null; videoEl = null; users = 0;
  };

  // ---------------------------------------------------------------- the layout editor (in the share and live popups)
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // `use`: 'live' (16:9) or 'share' (9:16). Returns HTML; call P.mount(use) after it is on the page.
  P.editor = (use, opt = {}) => {
    const lay = P.get(use), modes = P.MODES.filter(([k]) => !(use === 'share' && k === 'beside'));
    return `<div class="pipEd" data-use="${use}"><b>Camera</b><div class="pipModes">${modes.map(([k, l]) => `<button type="button" class="${lay.mode === k ? 'on' : ''}" data-pipmode="${k}">${esc(l)}</button>`).join('')}</div>` +
      `<div class="pipRow"><canvas class="pipPrev ${use === 'live' ? 'land' : 'port'}" title="Drag the box to move it"></canvas><div class="pipSide">` +
      `<label class="pipSize">Size <input type="range" min="0.14" max="0.6" step="0.01" value="${lay.s}" data-pipsize></label>` +
      (opt.mic ? `<label><input type="checkbox" data-pipmic ${lay.mic ? 'checked' : ''}> Add my microphone (use headphones)</label>` : '') +
      `<p class="hint pipHint"></p></div></div></div>`;
  };
  let raf = 0;
  P.mount = (use, opt = {}) => {
    const root = document.querySelector(`.pipEd[data-use="${use}"]`);
    if (!root) return;
    const cv = root.querySelector('.pipPrev'), g = cv.getContext('2d'), hint = root.querySelector('.pipHint');
    const W = use === 'live' ? 320 : 180, H = use === 'live' ? 180 : 320;
    cv.width = W * 2; cv.height = H * 2; cv.style.width = W + 'px'; cv.style.height = H + 'px';
    let cam = null, closed = false;
    const sync = () => {
      const lay = P.get(use);
      root.querySelectorAll('[data-pipmode]').forEach((b) => b.classList.toggle('on', b.dataset.pipmode === lay.mode));
      root.querySelector('.pipSize').style.visibility = lay.mode === 'box' || lay.mode === 'big' ? 'visible' : 'hidden';
      hint.textContent = { none: 'Only the beat is shown.', box: 'Drag the camera box anywhere.', above: 'Your camera sits above the beat.', beside: 'Your camera sits beside the window, covering nothing.', big: 'Your camera fills the frame; drag the beat box anywhere.' }[lay.mode] +
        (use === 'share' && lay.mode !== 'none' ? ' The clip records in real time while the track plays, so you can react on camera.' : '');
    };
    const draw = () => {
      if (closed || !document.body.contains(cv)) { stop(); return; }
      raf = requestAnimationFrame(draw);
      P.compose(g, cv.width, cv.height, P.get(use), (gg, x, y, w, h) => {
        if (opt.drawMain) return opt.drawMain(gg, x, y, w, h);
        const gr = gg.createLinearGradient(x, y, x + w, y + h); gr.addColorStop(0, '#1b1d27'); gr.addColorStop(1, '#2a1f10');
        gg.fillStyle = gr; gg.fillRect(x, y, w, h);
        gg.fillStyle = '#e39a12'; const n = 14, slot = (w * 0.8) / n;
        for (let i = 0; i < n; i++) { const bh = h * (0.12 + 0.3 * Math.abs(Math.sin(i * 1.7 + performance.now() / 400))); gg.fillRect(x + w * 0.1 + i * slot, y + h / 2 - bh / 2, slot * 0.6, bh); }
        gg.fillStyle = '#ede9e0'; gg.font = `600 ${Math.max(10, h * 0.07)}px -apple-system, "Segoe UI", sans-serif`; gg.textAlign = 'center'; gg.textBaseline = 'alphabetic';
        gg.fillText(use === 'live' ? (opt.mainLabel ? opt.mainLabel() : 'STRATUM window') : 'Your beat', x + w / 2, y + h * 0.85);
      }, cam && cam.video);
    };
    const stop = () => { cancelAnimationFrame(raf); raf = 0; if (cam) { P.closeCamera(); cam = null; } closed = true; };
    const startCam = async () => {
      if (cam || !P.camera(P.get(use))) return;
      try { cam = await P.openCamera(false); } catch (e) { hint.textContent = 'Camera preview unavailable: ' + (e.message || e); }
    };
    root.addEventListener('click', (e) => {
      const b = e.target.closest('[data-pipmode]'); if (!b) return;
      P.set(use, { mode: b.dataset.pipmode }); sync(); startCam();
    });
    root.addEventListener('input', (e) => {
      if (e.target.matches('[data-pipsize]')) P.set(use, { s: +e.target.value });
      if (e.target.matches('[data-pipmic]')) P.set(use, { mic: e.target.checked });
    });
    // Drag the box (the camera box, or the beat box in "camera big").
    let drag = null;
    cv.addEventListener('pointerdown', (e) => {
      const lay = P.get(use); if (lay.mode !== 'box' && lay.mode !== 'big') return;
      const r = cv.getBoundingClientRect(); drag = { r }; cv.setPointerCapture(e.pointerId); move(e);
    });
    const move = (e) => { if (!drag) return; P.set(use, { x: clamp((e.clientX - drag.r.left) / drag.r.width, 0, 1), y: clamp((e.clientY - drag.r.top) / drag.r.height, 0, 1) }); };
    cv.addEventListener('pointermove', move);
    cv.addEventListener('pointerup', () => { drag = null; });
    P.unmount = stop;
    sync(); cancelAnimationFrame(raf); draw(); startCam();
  };
})();
