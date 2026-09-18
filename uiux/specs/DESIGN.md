# ADHD Fairy — final design specification

Revision 4 · 14 September 2026 · Implementation handoff for the existing Mac app and Fairy Home web app.

## Authority and reading order

The owner has now explicitly supplied and requested the final design. This satisfies the earlier builder pack's instruction to wait for owner direction before creating design.md. Preserve all unrelated repository instructions, privacy rules, read-only integrations and existing architecture. This handoff replaces previous visual and gamification handoffs; do not merge old economy rules into it.

Read this file, GAMIFICATION.md, specs/bloom-timer-v1.md, IMPLEMENTATION.md, SCREEN_MATRIX.md and ASSETS.md. Machine-readable catalogs and tokens are in specs/. README.md includes a ready-to-paste Xcode Codex instruction. Use the runnable prototype and references/final-*.png as implementation evidence. Approved concept images establish mood and composition; illustrative numbers/text in them do not override these rules.

## Final decisions

- Main Mac window IS the cottage hub. Web Fairy Home uses the same information architecture.
- Automatic milestone **charms** replace badges. There is no Stardust, balance, store, purchase, price, saving goal, equip system or pinning.
- Collection contains **Your charms / Discover / Garden**.
- New shelf starts empty. Earned charms sit on wood, never hover. One Fairy sits at the right edge of the first shelf.
- Shelf content is constrained in width. Do not stretch one tile across a large desktop window.
- Discover shows only unearned charms, requirements and numeric progress bars. No Fairy, library scene or decorative scene rail on Discover.
- All six quest covers are immediately available; select when creating a quest and edit later. No unlocking or costs.
- One flower requires four completed 25-minute focus blocks. Short sessions contribute to the same plant. Flowers live in Garden.
- Fairy has a blonde bun, lavender petal dress/wings, natural arms, no satchel/straps. She reads spells at home and goes on forest quests, never uses a computer.
- Real pixel artwork and licensed font files are included. Never replace collectible icons with emojis.

## Visual system

The intended feeling is a quiet, useful magical library. Keep a few intentional objects and broad readable surfaces. Do not add ornamental vines everywhere, dense sparkles, oversized slogans, glass effects, or dashboard-like giant tiles.

| Token | Value | Use |
| --- | --- | --- |
| Surface | #FAF6EE | Main cream background |
| Soft surface | #F5EFE5 | Secondary planes |
| Ink | #35214F | Text |
| Muted ink | #665672 | Supporting text |
| Lavender | #DED0ED | Selected tabs, quiet highlights |
| Primary | #594071 | Main buttons with white text |
| Outline | #705584 | Strong frame |
| Divider | #D9D0D7 | Subtle boundaries |
| Progress | #9AB58D | Sage fill |
| Progress track | #E5D9ED | Lilac background |

Pixelify Sans Bold (bundled WOFF2/TTF, SIL OFL) for headings and clock; system sans for body, requirements, buttons and paragraphs. Default body16, supporting14, compact supporting12–13, title28–32, section20–24. Use readable text and Dynamic Type; do not bake labels into art. Spacing4/8/12/16/24/32/40. Main controls44 high, compact36 where needed with adequate separation. Thin1–2px borders, modest4–7px corners, restrained offset shadows. Selected controls use a visible border/check as well as color.

Default light appearance is the approved shipping target. The supplied cream-backed atlases need alpha exports or deliberate surface matching before a production dark theme. Do not offer an unverified theme that leaves mismatched art rectangles.

## Main shell

Reference window max1220 logical px in HTML; sidebar190 default with compact breakpoint155; native titlebar about46. Use actual native traffic lights, not duplicate fake controls. Content padding24–32, gap24. At wide sizes keep Collection work area max760 centered in remaining space. At narrow browser widths the sidebar becomes wrapping labeled navigation; cards stack. Native minimum sizing should preserve usable text and composer, not force a fixed screenshot size.

Routes: Today, Talk, Inbox, Quests; Collection and Settings lower. Focus, wrap-up, quest detail, Garden and Discover are child surfaces, not additional permanent sidebar clutter. One primary next action. Main data scrolls; drafts and timer state survive route/window changes.

## Today

Curated library illustration may occupy a small right rail. One next-action card, energy/capacity chooser Low/Medium/High/Survival, editable daily plan with Anchor/Quest/Maintenance/Optional categories. Always include Add task and inline quick add; allow editing title/category and removing tasks. Selecting a task checkbox explicitly completes it. Optional work is not a forced quota.

Quick capture saves to Inbox without scheduling. A compact growing-plant shortcut opens the shared timer. Real recommendations must use real calendar capacity and buffers, show honest unavailable state, and not recommend impossible session lengths. Demo recommendations are static sample copy.

## Main Talk and popup chat

Main Talk has a constrained readable transcript, user/Fairy message distinction and a pinned multiline composer. Use the whole small speaking Fairy asset with contain fitting; no duplicate corner Fairy or scene rail. A small shared timer status strip links to Focus. Maintain a shared thread/draft between surfaces. Show real loading, stopped generation, retry and offline states only when applicable; preserve unsent text on error. Proposed AI tasks need explicit review before insertion.

Quick chat is vertical, width320 logical px, header44; approximately560 content height when space permits. Timer above transcript; transcript scrolls; composer remains visible at bottom. Clamp total panel height to usable monitor bounds. At very short heights allow timer collapse or body scroll; never obscure Send. One speaking Fairy per assistant message; no additional character in header, corner or timer card. No library background in quick chat. Chat remains accessible while timing; closing the panel does not pause the timer.

## Inbox

A thought basket with pixel envelope/book accents, readable note rows, compact capture form. Review reveals Task / Quest / Someday / Note and explicit Save. A Task becomes Optional Today; Quest becomes a draft with default Lavender cover; notes/someday remain unscheduled. Production preserves capture provenance and supports undo. One small floating Fairy may occupy safe bottom whitespace, never cover a row or button. No urgency count badges or pretend completion checkboxes. Empty state is calm.

## Quest books and cover picker

Quest shelf uses cute pixel book covers and a forest scene, with title, step progress and New Quest. Covers are cosmetic only. Six IDs: lavender, moss, rose, midnight, honey, sky. Lavender default. The selected cover persists per quest; many quests may reuse the same cover.

Create dialog: title 'A new adventure', name field, 'Choose your cover', short note 'All covers are yours. Change it anytime.', 3-by-2 radio choice grid, Cancel/Create quest. Max570 width; scroll within available height. Cover options show whole book, name and selected check/border. Keyboard arrow/radio behavior works. Require a nonblank title; do not require steps to create a draft. Saving stores one coverID; cancel must discard changes. Editing uses the same picker; changing cover never modifies steps, rewards or focus.

Detail shows selected book, title, Edit name & cover, steps and fraction, Add step and Start with me. Empty draft has no completion button. Finish Quest is explicit after at least one required step exists and all required steps are done. Completed books remain. Reopening/recompleting never repeats a milestone credit. Production optional or superseded steps must be excluded from required denominator.

## Your charms shelf

Main work max760px, refined heading, collection tabs. Shelf panel padding24 and fine lavender border, no scene rail. First row reserves three charm positions and a fourth seated-Fairy position. Further rows allow four charms. Two rows initially; append rows as earned items require, keeping the first-row Fairy fixed. No individual placement or rearranging in V1. Order by earned timestamp, catalog order for ties.

Charms are about90–104 high on desktop, about50–65 on narrow screens. Asset bases touch shelf top. Put names BELOW wood, not between icon and shelf. Use source-rect crops and consistent bottom anchors, never invisible bitmap padding as the contact baseline. Seated Fairy uses genuine alpha; hands/seat align with wood and feet dangle below; head/wings/feet intact. No duplicate Fairy. Shelf shape is reproducible CSS/SwiftUI geometry in V1; pixel scene artwork is not a full-screen image with fake buttons.

Fresh account: zero charms, empty shelves and seated Fairy with brief first-task hint. Do not pre-award samples. Each new charm shows a small New marker until its detail is viewed. Selecting a charm shows art, name, milestone and date; no buy/equip controls. Earned charms are permanent. A congratulations popup is temporary, never a permanent side tile.

## Discover

Same max760px main work area. Discover tab selected. Two columns of compact cards desktop, one column below520px. Cards approximately360–375 wide, about165 high, padding16–18, gap14; icon70–85. Title and one-line/two-line requirement next to icon, sage progress bar and exact n/threshold text. Page scrolls for the full catalog; no horizontal stretch. Do not force all 18 cards into one viewport.

Only unearned charms appear, in catalog order. Counts cap visually at threshold. Upon earning, charm moves to shelf automatically. No Fairy, library scene, shelf boards, 'buy' or 'claim' buttons. Header/subtitle are enough; omit repeated giant Not yet earned badges. All-discovered state acknowledges completion without inventing new obligations.

## Congratulations

Automatic unlock is persisted before celebration. One compact centered modal with pixel art, 'A little magic, earned!', charm name, fulfilled milestone, 'Added to your charms shelf.', Lovely!/View shelf. Multiple new charms share one popup with a scrollable list. Escape/dismiss acknowledges presentation, not ownership. Persist dismissal before navigation to avoid repeating on reload. Do not interrupt running focus; queue until focus pauses or transitions to break/complete. Quiet celebrations still unlock and show shelf New markers, with no modal. No automatic sound; reduced motion removes optional sparkles.

## Garden and Focus

Garden is separate from unique charms: flowers can repeat. It shows Growing and Bloomed species/counts/dates. A first flower also unlocks the Daisy milestone charm once. Pots are plain terracotta, NO hearts. All timer details, break accounting, persistence, sleep and stage thresholds are in specs/bloom-timer-v1.md.

Focus uses plant/current countdown/next step, four-part total-growth bar, cumulative focus minutes and start/pause/resume/save. A10-minute session grows a sprout; it is not a completed flower. Save/wrap-up stores an optional return note and does not mark the task complete automatically. Rescue suggests a smaller step without punishment.

## Desktop Fairy, hover, icon and widget

Floating Fairy ~88–140 high depending user size, optional32px pixel icon. Hover or keyboard focus offers a brief240px peek: task and shared remaining time. Never steal focus. Click opens chat; drag threshold5pt avoids accidental opening. Native panel bounds persist and clamp after monitor changes; hide/reopen and menu-bar access remain. App icon source is included; catalog export still needed. Widget preview uses the same plant/time and opens the cottage or focus action. Real WidgetKit updates and native overlay behaviors require integration in the Xcode project.

## Accessibility and integration

Text scales; keyboard access and visible focus for every action; radio labels and selected states; programmatic progress values; text alternatives from surrounding controls. Decorative atlas sprites hidden from VoiceOver. Announce milestone/phase transitions, not every countdown tick. Native app observes one shared service, not one timer/reward engine per window. Preserve established chat/calendar/auth boundaries. See IMPLEMENTATION.md for data, failures, transactions, migration and test gates.
