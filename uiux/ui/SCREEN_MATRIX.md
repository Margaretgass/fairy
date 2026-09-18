# Screens and state coverage

All16 primary routes are available in the HTML Preview selector. Use the two preview disclosures for fixture states. Production error paths below are specified for the existing app even when no real connection exists in the demo.

| Route | Main purpose | Included demo behavior |
| --- | --- | --- |
| today | Cottage hub | Add/edit/remove/complete tasks, capacity, quick capture, timer shortcut |
| talk | Full chat | Shared thread/draft, multiline composer, scripted replies, timer strip |
| inbox | Thought basket | Capture, review, convert Task/Quest/Note/Someday; one Fairy |
| quests | Book shelf | Named quest books with selected covers, new quest |
| quest | Quest detail | Add/check steps, explicit Finish, edit name/cover |
| questcreate | Cover form preview | Six free choices with check/border, name, create/cancel |
| focus | Full flower timer | Start short/full, pause/resume, grow stages, break and bloom |
| wrap | Session wrap-up | Outcome and saved return note; task remains separate |
| collection | Your charms | Empty/earned/full shelf; seated Fairy; detail/New status |
| discover | Unearned charms | Compact two-column progress cards; no Fairy/scene |
| garden | Plants | Current growth, earned species/counts/dates |
| popup | Vertical quick chat | Shared flower state, transcript and reachable composer |
| companion | Floating Fairy demo | Hover/focus peek, drag, hide/icon, quick chat |
| widget | Icon/widget concept | Supplied icon and shared flower/time preview |
| settings | Preferences | Quiet celebrations, companion access, honest connection status |
| insights | Observation placeholder | Honest no-insights state and quest shortcut |

Additional visible states: congratulations single/batch, charm details, new/edit quest dialog, cancelled selection, first three charms, regular user, full18-charms shelf, all-discovered state, seed/sprout/leaves/tall/bud/bloom, focus/break pause, waiting for manual next block. Developer fixtures never alter saved progress.

Current actual screenshots: references/final-*.png. SCREENS.html is the visual index. Approved concepts: concept-charms-shelf.png, concept-discover.png, concept-cover-picker.png. They are visual guides, not sources for incidental numbers. Library/forest concepts are retained only for Today/Quest scene mood.

Production states to wire to actual repository: loading, empty, offline, stale context, disconnected integration, save pending/failure/retry, AI streaming/stop/error, multi-device conflicts, native panel clipping/monitor changes. No fake connected accounts or pretend live AI. Browser local persistence does not prove shared backend/native readiness.
