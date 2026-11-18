// Checks the app's update comparison and banner logic (web/js/update.js) with stand-ins for the page: node tests/update-check-test.mjs
import fs from 'node:fs';
import vm from 'node:vm';

let fails = 0;
const check = (ok, what) => { console.log((ok ? 'ok   ' : 'FAIL ') + what); if (!ok) fails++; };
const run = async ({ host, alpha, answer, fetchFails, ask }) => {
    const toasts = [], els = {}, calls = { fetch: 0 };
    const doc = { getElementById: (id) => els[id] || null, createElement: () => ({ dataset: {}, set innerHTML(v) { this.html = v; } }), body: { appendChild: (e) => { els[e.id] = e; } } };
    const S = { ALPHA: alpha, ui: { toast: (m, bad) => toasts.push([m, !!bad]) }, io: { host: () => host, native: () => null }, plug: { ask: async () => ({}) } };
    const sb = { window: { S }, document: doc, setTimeout: (f) => { sb.later = f; return 1; }, clearTimeout() {}, AbortController, console,
        fetch: async () => { calls.fetch++; if (fetchFails) throw new Error('offline'); return { ok: true, json: async () => answer }; } };
    sb.window.S = S; vm.createContext(sb);
    vm.runInContext(fs.readFileSync(new URL('../web/js/update.js', import.meta.url), 'utf8').replace('const S = window.S, IO = S.io, U = S.ui;', 'const S = window.S, IO = S.io, U = S.ui;'), sb);
    if (ask !== undefined) await S.update.check(ask);
    return { S, toasts, bar: els.updateBar, calls, sb };
};

let t = await run({ host: true, alpha: '11.3', answer: { alpha: '11.3' } });
check(t.S.update.newer('11.10', '11.9') && !t.S.update.newer('11.9', '11.10') && !t.S.update.newer('11.3', '11.3') && t.S.update.newer('12', '11.9') && t.S.update.newer('11.3.1', '11.3'), 'version order is numeric ("11.10" is newer than "11.9")');

t = await run({ host: true, alpha: '11.3', answer: { alpha: '11.4', page: 'https://site.test/#download' }, ask: false });
check(t.bar && !t.bar.hidden && /11\.4/.test(t.bar.html) && t.bar.dataset.page === 'https://site.test/#download', 'a newer alpha shows the update bar with the download page');

t = await run({ host: true, alpha: '11.3', answer: { alpha: '11.3' }, ask: false });
check(!t.bar && !t.toasts.length, 'the same alpha shows nothing on launch');

t = await run({ host: true, alpha: '11.3', answer: { alpha: '11.3' }, ask: true });
check(!t.bar && /newest/.test(t.toasts[0][0]), 'Check for updates says you are up to date');

t = await run({ host: true, alpha: '11.3', answer: {}, fetchFails: true, ask: false });
check(!t.bar && !t.toasts.length, 'a failed check on launch stays silent');

t = await run({ host: true, alpha: '11.3', answer: {}, fetchFails: true, ask: true });
check(t.toasts[0][1] && /Could not check/.test(t.toasts[0][0]), 'a failed check from Help says so');

t = await run({ host: true, alpha: '11.3', answer: { alpha: '<script>' }, ask: true });
check(!t.bar && t.toasts[0][1], 'a nonsense answer is refused');

t = await run({ host: true, alpha: '11.3', answer: { alpha: '11.4', page: 'http://evil.test/' }, ask: false });
check(t.bar.dataset.page.startsWith('https://stratum-studio-pi.vercel.app'), 'a non-https page address is replaced by the site');

t = await run({ host: false, alpha: '11.3', answer: { alpha: '11.9' }, ask: true });
check(t.calls.fetch === 0 && !t.bar && /updates itself/.test(t.toasts[0][0]), 'the web app never calls the site and says it updates itself');

console.log(fails ? fails + ' failed' : 'all passed');
process.exit(fails ? 1 : 0);
