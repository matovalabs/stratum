// The newest alpha, for the Mac and Windows apps' update check. Public: it only says which version is current.
import { env, json, origin } from '../lib/gate.js';

export function GET(request) {
    const tag = env('DOWNLOAD_TAG'), m = tag.match(/alpha\.([0-9]+(?:\.[0-9]+)*)$/);
    if (!m) return json({ error: 'no version set' }, 404);
    return json({ alpha: m[1], tag, page: origin(request) + '/#download' });
}
