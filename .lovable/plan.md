# EmotionSense AI — Frontend UI Plan

Build a premium, minimal SaaS-style dashboard with warm-white/beige palette and dark-brown accent. Frontend only — no backend or AI logic; placeholders where APIs will hook in later.

## Design tokens (src/styles.css)
Update `:root` to the requested palette:
- `--background`: #FAF8F5 (warm white)
- `--secondary`: #F2ECE5 (soft beige)
- `--card`: #FFFFFF
- `--foreground`: #111111
- `--primary`: #5C4033 (dark brown) + `--primary-foreground` white
- `--border`: #E5E5E5
- `--radius`: 1rem (16px)
- Sidebar tokens aligned to the same palette
- Soft shadow utility, medium font weights, Inter font loaded via `<link>` in `__root.tsx`

## Routes (src/routes/)
- `__root.tsx` — update head meta (title "EmotionSense AI", description), load Inter font, wrap `<Outlet />` in `AppLayout`
- `index.tsx` — Dashboard (two action cards + stats)
- `history.tsx` — History table
- `settings.tsx` — Settings cards
- `about.tsx` — About page

Live Detection and Upload Image are modals triggered from the Dashboard (and sidebar entries), not routes. Sidebar entries for those two open the same modals via shared state in `AppLayout`.

## Components (src/components/)
- `app-layout.tsx` — Shell: collapsible sidebar + top nav + `<Outlet />`; owns modal open state for Live Detection / Upload
- `app-sidebar.tsx` — Uses shadcn `Sidebar` with `collapsible="icon"`; items: Dashboard, Live Detection, Upload Image, History, Settings, About (lucide icons)
- `top-nav.tsx` — Logo mark, "EmotionSense AI" title, optional search input, avatar (shadcn Avatar + DropdownMenu)
- `dashboard/action-card.tsx` — Large card with icon, title, description, CTA button; hover elevation
- `dashboard/stats-grid.tsx` — 4 stat cards (Current Model / Dataset / Avg Accuracy / Total Scans)
- `modals/live-detection-modal.tsx` — shadcn Dialog, large size, backdrop blur; left webcam preview placeholder (`<div>` with aspect-video), right panel (Current Emotion, Confidence, Detected Faces, FPS, Connection Status), bottom emotion timeline placeholder, buttons: Start Camera / Stop Camera / Capture Screenshot / Close
- `modals/upload-image-modal.tsx` — shadcn Dialog; drag-and-drop zone + Browse Files; result placeholders (Uploaded Image, Detected Face, Emotion, Confidence, Probability Chart placeholder); Analyze / Close buttons
- `history/history-table.tsx` — Search input, filter Select, Export button, shadcn Table (Date, Method, Emotion, Confidence, Status badge) with empty state
- `settings/settings-cards.tsx` — Camera Select, Confidence Threshold Slider, Theme Select, Notification Switch, Bounding Box Switch, Animation Switch, Save button
- `about/about-sections.tsx` — Cards for FER2013, TensorFlow, OpenCV, CNN Architecture, FastAPI, and an AI pipeline strip with lucide icons

## Animations
Use existing tailwind animation utilities (`animate-fade-in`, `hover-scale`) plus subtle Tailwind `transition` classes for hover elevation. No Framer Motion install needed for this pass (can add later if requested).

## Out of scope (placeholders only)
- Webcam capture, image analysis, FastAPI calls
- Real history data (empty state)
- Persisting settings

## Head metadata
Each leaf route gets its own `head()` with unique title + description + og tags.
