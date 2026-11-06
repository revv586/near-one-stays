# Facebook → GitHub Pages sync

## Scope and access

Read only these two public groups using the authorized browser session:

- https://www.facebook.com/groups/691988518250398
- https://www.facebook.com/groups/1116528203018291

The user has authorized reading these groups, committing to `main`, and deploying this public site. Do not contact anyone, open Messenger or private information, join groups, export cookies/passwords/session data, or bypass safeguards. Scope DOM inspection to the main feed, group search results, or the rental post being reviewed. Login failure or a security block is a failed collection, not a reason to extract credentials or probe alternate access paths.

## Start with current data

Read the latest repository versions of `dist/data/facebook-posts.json` and `dist/data/listings.json` before editing. Never replace current records with an older local snapshot. Preserve existing properties and unrelated sources. Re-read the Facebook JSON before uploading if another collector may have committed during the review; merge reviewed changes into that newest version.

Read newly loaded posts and, as useful, group searches for MRT ลุมพินี, คลองเตย, สามย่าน, งามดูพลี, พระราม4, หัวลำโพง, สีลม, สุขุมวิท and ศูนย์ฯสิริกิติ์. Limit each round to about 30 actually loaded posts per group. Open relevant rental posts, record their canonical permalink and the date label displayed on the post. Do not import requests from people looking for a room as rental offers. Do not claim complete group coverage.

## Review each offer

- Budget is at most ฿10,000/month. Prioritize 1 or 3–4 month contracts; separate 6 months. Unknown short-term price or minimum lease may remain a lead. Never turn an annual price into a short-term offer.
- Only MRT หัวลำโพง / สามย่าน / สีลม / ลุมพินี / คลองเตย / ศูนย์ฯสิริกิติ์ / สุขุมวิท, at most three stations from Lumphini. Prioritize Lumphini, Rama IV and Ngam Duphli for One Bangkok.
- Private rooms suitable for a male tenant; prioritize private bathrooms. Do not infer bathroom type, gender eligibility, shortcuts, or availability. Shared facilities must be labeled as alternatives.
- Actual walking route to an accessible station entrance ≤500m is primary; 501–800m is backup; >800m is excluded. A poster's distance, straight-line measurement, or route to a generic station point is not a verified entrance walk. Keep claimed distance separate from verified walking fields.
- Record rent by contract, deposit, advance, electricity, water, service fees and advertised availability only when stated. Unknown values stay unknown. Full or future rooms are not ready-to-rent rooms. `ownerConfirmed` remains false without direct confirmation; this task does not contact owners.
- Deduplicate building aliases while preserving individual unit offers and their sources. Retain exclusions with reasons for audit rather than recommending them as matching rooms.

## Honest attempt and success metadata

Update `dist/data/facebook-posts.json` using its current schema. For a successful group read set that group's `status: "ok"`, `lastCheckedAt`, and `lastRun` with the actual read time, number of posts read, and queries used. The top-level `lastRun` records actual attempt end time, status, successful/failed group counts, posts read/added/changed, scope, and summary. Use ISO timestamps with timezone.

On blocked/login/error, keep previous properties and the group's last successful `lastCheckedAt` unchanged; set that group's current `status: "blocked"` and a failed `lastRun` with attempt time and reason. Set the overall latest attempt to `blocked` or `partial` as applicable. Do not bump top-level successful `checkedAt` when the read did not succeed. No browser or no write access means the run did not complete. Never claim a sync merely because a task was scheduled.

Property `lastFetchedAt`, `lastReviewed`, factual dates and source poster dates must not advance from a group scan alone. Change property review times only after opening and reviewing that specific post. Record dates as displayed when absolute dates cannot be determined; do not substitute crawl time. A successful scan with no new matching posts still updates collection metadata and is deployed without sending a routine user alert.

The UI evaluates both group success timestamps, not just global `checkedAt`, and warns after 90 minutes. It distinguishes collection activity from the accumulated imported record count and individual room reviews.

## Save and deploy

Prefer the GitHub connector for reads and writes. If a write is rejected with integration 403 and the authorized signed-in GitHub browser is available, the existing fallback is:

1. Prepare a root `near-one-source.zip` containing only `dist/data/facebook-posts.json` and any new public post photos under `dist/assets/`. Inspect all archive members before upload. Never include `listings.json`, `.github`, `.git`, credentials, session material, or unrelated files in a collector payload.
2. Use GitHub's **Add file → Upload files** on `revv586/near-one-stays`, upload the ZIP, and commit to `main`. Wait for upload completion before committing. Do not overwrite unrelated current files.
3. The existing **Hourly refresh and deploy** workflow extracts the delta, merges Facebook input with the latest catalogue, refreshes other supported sources, runs `npm test` and `npm run build`, commits refreshed data, removes the ZIP, and deploys Pages. Do not treat the upload commit alone as completion.
4. Follow the run associated with the upload commit until refresh and deploy both succeed. Read failure logs if needed; preserve data rather than bypassing validation.
5. Open the deployed site and `data/facebook-posts.json` with a cache-busting version. Verify the new collection metadata and any reviewed post changes are actually live. Check that the per-property timestamps were not falsely advanced. Only then report a successful update.

For code/UI maintenance, a separately reviewed delta ZIP may include source, tests and docs, but must exclude both current data JSON files so an hourly collector's new records are not overwritten.

## Notifications

Notify in Thai only for a new matching room, a price reduction, a material contract/availability change, or a connection issue requiring user help. A normal no-change round records its result on the site without frequent user notifications. Report access limits accurately; never claim to have read every post.
