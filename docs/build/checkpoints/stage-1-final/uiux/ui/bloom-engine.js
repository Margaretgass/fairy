/* Dependency-free reference domain engine. Time in integer milliseconds. */
(function (root) {
    'use strict';
    const MIN = 60000, BLOCK = 25 * MIN, BREAK = 5 * MIN, TARGET = 4 * BLOCK;
    const species = ['Daisy', 'Lavender', 'Rose', 'Sunflower', 'Bluebell'];
    function create(id, pick, now, collection = []) { return { version: 1, plant: { id, species: species[Math.min(4, Math.max(0, Math.floor(pick * 5)))], focusMs: 0, plantedAt: now }, phase: 'ready', remainingMs: BLOCK, anchorMs: now, collection: [...collection] }; }
    function stage(s) { let m = s.plant.focusMs / MIN; return m >= 100 ? 'Bloomed' : m >= 75 ? 'Bud' : m >= 50 ? 'Growing tall' : m >= 25 ? 'Leaves' : m >= 10 ? 'Sprout' : 'Seed'; }
    function tick(s, now) {
        s = structuredClone(s); if (!['focus', 'break'].includes(s.phase)) return s; let elapsed = Math.max(0, now - s.anchorMs); s.anchorMs = Math.max(now, s.anchorMs); let used = Math.min(elapsed, s.remainingMs); s.remainingMs -= used;
        if (s.phase === 'focus') { s.plant.focusMs = Math.min(TARGET, s.plant.focusMs + used); if (s.remainingMs === 0) { if (s.plant.focusMs === TARGET) { s.phase = 'bloomed'; if (!s.collection.some(x => x.id === s.plant.id)) s.collection.push({ ...s.plant, bloomedAt: now }); } else if (s.plant.focusMs % BLOCK === 0) { s.phase = 'break'; s.remainingMs = BREAK; } else { s.phase = 'pausedFocus'; } } }
        else if (s.remainingMs === 0) { s.phase = 'ready'; s.remainingMs = BLOCK; }
        return s;
    }
    function start(s, now, minutes = 25) { s = tick(s, now); if (s.phase === 'pausedBreak') { s.phase = 'break'; s.anchorMs = now; return s; } if (!['ready', 'pausedFocus'].includes(s.phase)) return s; if (!Number.isFinite(minutes) || minutes <= 0) return s; s.phase = 'focus'; s.remainingMs = Math.min(Math.round(minutes * MIN), BLOCK - s.plant.focusMs % BLOCK); s.anchorMs = now; return s; }
    function pause(s, now) { s = tick(s, now); if (s.phase === 'focus') s.phase = 'pausedFocus'; else if (s.phase === 'break') s.phase = 'pausedBreak'; return s; }
    function resume(s, now) { return s.phase === 'pausedFocus' ? start(s, now, s.remainingMs / MIN || 25) : start(s, now); }
    function next(s, id, pick, now) { return s.phase === 'bloomed' ? create(id, pick, now, s.collection) : s; }
    const api = { MIN, BLOCK, BREAK, TARGET, species, create, stage, tick, start, pause, resume, next }; if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Bloom = api;
})(globalThis);
