# Automatic Charms — final V1 rules

There is no currency. Charms replace all previous badges and purchasable cosmetic rewards. All charms unlock automatically from fixed milestones and appear on one shelf. Quest covers are free cosmetic choices. Flowers remain in Garden with the existing four-block cycle.

## Catalog

The source-readable catalog is specs/charm-catalog.json; JavaScript mirror is prototype/charm-engine.js. Every ID is permanent. Display order is not a prerequisite sequence.

| ID | Name / artwork | Metric | Threshold |
| --- | --- | --- | ---: |
| star | First Spark / Star | Completed tasks | 1 |
| matcha | A Little Momentum / Matcha | Completed tasks | 5 |
| potion | Something Magical / Potion | Completed quests | 1 |
| lantern | Welcome Home / Lantern | Distinct active days | 3 |
| daisy | In Bloom / Daisy | Flowers grown | 1 |
| coffee | Finding Your Rhythm / Coffee | Completed tasks | 25 |
| spellbook | Next Chapter / Spellbook | Completed quests | 5 |
| key | A Familiar Place / Cottage Key | Distinct active days | 10 |
| basket | Little Garden / Flower Basket | Flowers grown | 5 |
| moon_potion | Moonlit Magic / Moon Potion | Completed tasks | 50 |
| book_stack | Keeper of Stories / Enchanted Book Stack | Completed quests | 15 |
| cottage | Right at Home / Glowing Cottage | Distinct active days | 30 |
| watering_can | Garden Keeper / Crystal Watering Can | Flowers grown | 15 |
| crystal_star | Quietly Powerful / Crystal Star | Completed tasks | 100 |
| compass | Forest Explorer / Enchanted Compass | Completed quests | 30 |
| teacup | A Season of Magic / Celestial Teacup | Distinct active days | 90 |
| terrarium | Flourishing / Moonflower Terrarium | Flowers grown | 30 |
| crown | Every Little Step / Golden Star Crown | Completed tasks | 250 |

New accounts have no charms. Star/Matcha/Potion are introductory milestones, not sequential gates. Finishing a quest before five tasks earns Potion immediately. A single action can unlock multiple charms. No duplicates, rarity, daily caps, purchases, claim step, equip/pinning, decay, streaks, artificial deadlines or penalties.

## Count exactly four things

1. Completed tasks: unique task/step IDs that have ever been explicitly completed. A quest step is a task; a daily projection of the same step must reuse its ID, not count twice. Unchecking, deleting, reopening or renaming never removes existing credit or reissues it. Recurring instances use distinct occurrence IDs. Creating/splitting/editing/importing an incomplete task does not count; superseded parent steps do not auto-complete.
2. Completed quests: unique IDs explicitly finished with at least one required step and all required steps complete. An empty draft never qualifies. Reopening cannot credit the same quest twice.
3. Flowers grown: unique plant IDs reaching100 focused minutes through the specified four-block state machine.10-minute sprout or25-minute block is not a flower. Background recovery can add flower credit, but does not itself create an active day.
4. Active days: distinct YYYY-MM-DD keys in the user's persisted IANA timezone on qualifying interactions. Saving a nonblank thought, sending a nonblank chat message, manually starting/resuming focus, completing a task or finishing a quest qualifies. App launch, background sync, navigation, typing without sending and passive timer ticks do not. Multiple actions/day count once; days need not be consecutive. Timezone changes affect future keys only; do not rebucket history. Browser reference uses device local timezone; production uses account preference.

Core task/quest events are the authority. Do not ask AI to judge effort, focus quality or eligibility. No attention surveillance. Counters are derived from stable credited IDs/records; store sets/unique records so replay and recount remain deterministic.

## Evaluate and persist

On each qualifying committed domain event: validate action, add its ID to the appropriate unique set, add eligible active-day key, compare all 18 catalog requirements, insert each newly eligible charm once, and queue its celebration. Save domain event, credit, new ownership and pending celebration in one existing-store transaction. A unique (userID,charmID) constraint and (userID,eventType,sourceID) credit constraint make retries safe. Native clients must not race separate copies of the evaluator.

Ownership row: charmID, earnedAt timestamp, seen flag. Pending presentation stores charmIDs, not new rewards. Requirement counts can come from the existing task/quest/flower history or a deduplicated credit table. Do not store private task/chat text inside reward records. Unique active days are bounded by lifetime days used; no per-keystroke event logging.

Present only after persistence succeeds. Failure keeps progress in memory/pending retry and shows a truthful save error; never announce a durable award that failed. Persist popup dismissal before closing/navigation. Closing a popup or ignoring it never loses ownership. Mark a charm seen when viewing its detail; opening the shelf alone does not erase all New markers. A crash before popup dismissal may show it again, but cannot award twice.

## Presentation policy

Shelf starts empty and fills in earned order. Discover contains unearned catalog entries and progress. Completion removes from Discover and adds to shelf. Show one congratulations popup per batch, with all newly earned charms. Defer while focus is running or another dialog is open; present at the next safe state (pause, break, completion, or dialog closure). Quiet celebrations suppress popups and acknowledge pending presentation after successful save, but preserve New markers. Sound off by default; no compulsory confetti.

## Migration

Do not convert previous balances, purchases or pins to rewards. No economy fields remain in the new UI. For an existing real account, compute eligibility from trustworthy historic unique completion and active-day records and unlock eligible charms once; do not fabricate missing historical usage. Migration can acknowledge historical pending popups as a batch summary instead of an 18-modal burst. Never delete task/history data to reset rewards. The supplied browser demo uses its own v4 key and intentionally does not import older sample data.

## Acceptance cases

- New account empty; first completed task Star; fifth distinct task Matcha; first completed quest Potion regardless of task count.
- Repeated event, undo/recomplete, daily mirror of same step, reopening quest, and retry after reload do not duplicate credit.
- Day1, day5 and day9 qualify for Lantern; three launches without interaction do not.
- Flower awarded once at fourth25-minute focus completion, Daisy charm once; another flower adds Garden count only until next milestone.
- Several thresholds reached together create one batch popup; dismiss/reload does not redisplay an acknowledged batch.
- During running focus, charms persist but popup waits; quiet mode still unlocks.
- Save failure does not falsely celebrate; retry is idempotent. Concurrent clients do not duplicate credit.
- No balance, prices, buy/equip/pin controls or gated book covers in any surface.

Reference tests: tests/charms.test.cjs (15 assertions), tests/bloom-engine.test.cjs (17 assertions), tests/browser-qa.cjs. Port meaningful domain tests into the existing Swift/TypeScript suites and test transactional integration in the actual project.
