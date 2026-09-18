# Asset manifest and rendering

| File | Use | Format/preparation |
| --- | --- | --- |
| assets/charms.png | All18 unique milestone charms | Cream-backed6×3 atlas; use exact measured source rectangles |
| assets/book-covers.png | Six free quest covers | Cream-backed3×2 atlas; use exact source rectangles, not naive square crops |
| assets/fairy-seated.png | Fairy on first charms shelf | RGBA with genuine alpha; seat anchor around70% of source height |
| assets/fairy-full.png | Speaking, Inbox and floating Fairy | Whole RGBA character; contain fitting |
| assets/flowers.png | Five growth stages and five species | Cream-backed5×2 atlas, plain terracotta pots, no hearts |
| assets/pixel-rewards.png | Existing navigation/inbox icons | RGBA4×3 atlas |
| assets/app-icon.png | App icon source | Prepare final opaque AppIcon catalog/export |
| assets/pixelify-sans-700.woff2 | Browser display headings | Bundled font |
| assets/PixelifySans-Bold.ttf | Native display headings | Register in target; PostScript PixelifySans-Bold |
| assets/FONT-LICENSE.txt | Font license | SIL Open Font License |
| assets/sprite-rects.json | Charms/covers pixel source rectangles | x,y,width,height in original image pixels; not points |

Charms atlas order is catalog art index0–17. Cover art index0–5 matches quest-covers.json. Source rectangles are also bundled in prototype/sprite-rects.js. Clip atlas images to the exact source rectangle before fitting them into a control; otherwise neighboring cells can leak into SVG letterboxing. The prototype uses explicit clip paths.

For native rendering use CGImage source cropping with these pixel rectangles, then .resizable().interpolation(.none).scaledToFit(). Preserve full art, labels separate. Do not use fill-cropping for character images. Seated Fairy's transparent canvas includes padding; align the actual seat to wood, not the image's bottom. In the reference HTML it is an overlay anchored to the last slot, with feet below the board. Charms use bottom-aligned source crops touching the board. Shelf geometry is CSS with warm wood colors and simple brackets, reproducible as SwiftUI shapes; no custom image processing required.

Cream atlas mattes match #FAF6EE approximately; generated artwork has slight tonal variation. They are not transparent sprites. Before shipping dark themes or different backgrounds, prepare proper alpha source assets and visually validate edges; do not claim transparent exports from these RGB files. Seated and standing Fairy alpha are genuine.

Library/forest source images under references/ contain baked mockup UI; the prototype uses illustration viewports only. Production still needs clean standalone scene layers if using those insets, and extra fairy animation poses if desired. V1 static character art is supplied and sufficient for the demonstrated screens. No scene art is needed on Charms/Discover/Garden.

Use the supplied generated art and licensed fonts, not scraped marketplace images. App icon export and native widget implementation remain target-project work. Treat approved concept screenshots as references, never interactive backgrounds for the whole page.
