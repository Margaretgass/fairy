# Bloom Timer V1 — authoritative behavior

This specification supersedes every older numeric-only timer and flower concept in this package. Implement these rules in the existing focus service; do not create a separate timer per screen. The JavaScript domain reference in prototype/bloom-engine.js is executable and tested. Port its behavior into the existing Swift model rather than embedding a second browser timer in the native app.

## The invariant

ONE FLOWER = FOUR COMPLETED 25-MINUTE FOCUS BLOCKS = 100 FOCUSED MINUTES.

Three required 5-minute breaks separate those blocks. Break time never grows a plant. Bloom and collection insertion occur at the end of focus block four. The final 5-minute break is optional and does not delay the flower. Thus the shortest earning path is 115 elapsed minutes; taking the optional final break makes 120. This timing is an explicit design choice for V1. Do not silently redefine a cycle as one 25-minute block.

A short session earns progress on the SAME plant, not a completed flower or separate sprout collectible. Ten minutes followed later by fifteen minutes completes block one; the first break then begins. Remaining blocks still require 25 minutes each. Growth persists across days. There is one growing plant at a time, not one per task.

## Growth thresholds (inclusive)

| Cumulative focus | Artwork | Collection status |
| --- | --- | --- |
| 0–less than 10 min | Seed in soil | Growing |
| 10–less than 25 min | Sprout | Growing |
| 25–less than 50 min | Leaves | Growing |
| 50–less than 75 min | Taller stem | Growing |
| 75–less than 100 min | Closed bud | Growing |
| Exactly 100 min | Species-specific flower | Bloomed, one permanent award |

Use milliseconds internally; thresholds refer to credited focus, not displayed rounded minutes. Countdown rounds remaining seconds upward. Numeric timer counts the current selected focus session or break; the four-segment growth bar shows cumulative plant focus. Labels must distinguish them.

## State transitions

| Current state | Event | Next state and mutation |
| --- | --- | --- |
| ready | Start 25 / Focus 10 | focus; cap duration to current block remainder |
| focus | Pause / Save for later | pausedFocus; credit elapsed focus first |
| pausedFocus | Resume | focus; remaining selected session duration; if short session already ended, use current block remainder |
| pausedFocus | Focus 10 | focus; choose fresh 10-minute cap, limited by block remainder |
| focus | Selected short duration ends before block boundary | pausedFocus; preserve growth; no automatic break |
| focus | Reach 25 / 50 / 75 cumulative minutes | break; start a 5-minute countdown |
| break | Pause / Save for later | pausedBreak; preserve break remainder |
| pausedBreak | Resume | break; continue same remainder |
| break | Five minutes complete | ready; next focus requires explicit Start |
| focus | Reach 100 cumulative minutes | bloomed; atomically insert one earned flower |
| bloomed | Plant another seed | ready with new plant ID/species; retain all earned flowers |

No skip-break or restart-growth button in V1. Optional final rest can be offered by the existing break service after bloom; it must not create a fifth focus block. The HTML ends on bloom and does not implement that optional final rest. Saving/wrapping a session never completes the task automatically. Task completion is a separate explicit action.

## Species and collection

Select Daisy / Lavender / Rose / Sunflower / Bluebell with equal probability once when creating the plant. Persist that selection before starting. Never reroll on resume, screen changes, reload, pause, or changing the task. UI reveals the name only on bloom; early artwork is common to all plants. Duplicates are allowed and counted. No rarity, paid rerolls, trading, selling, or duplicate currency conversion in V1.

Store Plant: id, species, focusMs, plantedAt, optional sourceQuestID.
Store FocusState: version, plant, phase, remainingMs, anchorMs.
Store EarnedFlower: plant ID as unique award key, species, focusMs=6000000, plantedAt, bloomedAt, optional sourceQuestID. Persist as a transaction with the transition to bloomed. Never duplicate on retries or two surfaces processing the same completion.

Collection has Your charms, Discover, Garden. Garden shows current Growing plant separately from Bloomed flowers. Species tiles show quantity and latest earned date. Undiscovered tiles are faint preview silhouettes, no purchase action. Prior flowers are permanent. Changing quests does not plant another seed or transfer ownership. Details may link to a quest but must not duplicate private task/chat text in reward records.

Flowers are separate from unique milestone charms: each new plant completion adds one Garden flower, with species duplicates allowed. The first flower and later catalog thresholds also unlock their associated charm automatically. No flower purchases or currency. Quiet celebrations do not stop plant growth or prevent charm unlocks.

## Suspension and durable state

Use a shared authoritative store/service for all Mac surfaces. Start/pause/resume are serialized commands. Persist on actions and app lifecycle changes; update display once per second. Rendering, opening/closing the popover, navigating, or hiding the fairy must not start, pause, or reset the timer.

Credit elapsed time only in the active phase, clamped to its remaining duration. If processing happens much later (sleep/relaunch), settle at most that one phase. If focus reached a boundary, the break starts when that boundary is processed. Never run through unattended future blocks or credit several flowers from a stale timer. Break completion waits for explicit next Start. This is intentional, even if it extends wall-clock cycle duration after suspension.

Use a monotonic clock while running and persist enough wall-clock information for restart reconciliation. Reference JS clamps negative clock deltas and retains a high-water anchor, but cannot resist manual clock tampering. Production should use the existing trusted clock/server policy when available. The browser v4 snapshot saves app, charms and Garden together. Browser localStorage is a demonstration, not an atomic multi-tab or multi-device store. Do not claim web/native synchronization until integrated and tested. Use revision/transaction guards and unique plant IDs for concurrent completion. Failure to persist keeps the user’s work in memory and offers retry; do not claim successful collection insertion before durable acknowledgement.

No attention surveillance: switching applications, using a permitted tool, dismissing chat, or declining a nudge does not kill a plant. Pausing saves progress. No death animation, lost earned flowers, or shame language in V1. Reduced motion shows stage changes without particles; sound off by default. Announce state changes accessibly, not each countdown tick.

## Artwork

assets/flowers.png: five columns, two rows. Top seed/sprout/leaves/tall/bud. Bottom daisy/lavender/rose/sunflower/bluebell. Plain terracotta pots, NO hearts. Cream-backed reference sprite atlas, not transparent. CSS uses 500% by 200% background size with column positions 0/25/50/75/100% and row 0/100%. Keep the full pot and plant inside each square; no clipping. Native implementation may use source-rect crops or prepare named assets. Match cream background or obtain alpha exports before dark-theme production use. Do not use emojis.

## UI surfaces

Main Focus: heading, plant and current countdown, task, four-segment growth bar, cumulative minutes, start/pause/resume/save, compact explanation. Support card lists four growth milestones. No duplicated countdowns.
Quick chat: 320 px wide, header 44 px, content about 560 px; timer card above scrollable messages, composer pinned bottom. At smaller screens allow popover height to fit available screen space and scroll the transcript. One speaking fairy avatar per assistant message; no extra fairy portrait in timer/header/corner. Full-body contain, never crop wings/head.
Main Talk: compact shared timer status strip + Open timer. Today: growing plant shortcut. Hover peek: task and current remaining time only; no large flower. Widget: same plant/time as a lightweight preview; native interactive WidgetKit wiring remains implementation work.

## Required tests

Run tests/bloom-engine.test.cjs. Port all acceptance cases into the native test suite. Also verify one shared timer across main window/popover/menu-bar, restart persistence, atomic once-only collection award, quiet celebrations, persistence errors, device sleep, DST/clock change, reduced motion, VoiceOver and window fitting. Only mark native tests as passed after running the actual project.
