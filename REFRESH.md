# AFA v2 dashboard — hourly refresh recipe (deterministic, keep output minimal)

Repo/working dir: `~/Documents/Claude/AFA_WorldCard_Tracking/v2live_repo`
Meta account `1915691362502143`. Campaigns: MY `120250933759090127`, SG `120250933759370127`, ID `120250933760930127`. Pixel `452951443891928`.

1. **Campaign totals** — `ads_get_ad_entities` level=campaign, date_preset=maximum, fields `["amount_spent","impressions","ctr","results","actions:link_click","reach","frequency"]`, filter campaign.id IN the 3 IDs. → region spend/impr/ctr/clicks/reach/freq, and `reg` = the `results` value (Website registrations completed; 0 until approvals land).
2. **Cells** — same call at level=adset, fields `["name","amount_spent","impressions","cpm","ctr","actions:link_click","cost_per_link_click","effective_status"]`. Map each ad set into its region's `cells` by name (`… Ad spend …` / `… Business spend …`). cpc = cost_per_link_click. st = effective_status simplified (ACTIVE→learning, PENDING_REVIEW→in review).
3. **Pixel funnel** — `ads_get_dataset_stats` dataset `452951443891928`, aggregation=event (it saves to a file). Then in Bash, sum `Registration-start / Registration-submit / CompleteRegistration / L3_submitted` over buckets with timestamp >= two days ago; write into `pixel`.
4. **Write `data.json`** (same schema, don't change structure). Set `updated_sgt` to current SGT ("YYYY-MM-DD HH:MM SGT"). Keep `budget_daily`, `budget` per region, notes as-is.
5. **Build + ship**: `cd` to the repo, `python3 build.py`, then `git add -A && git -c user.name=socialworldfirst -c user.email=socialworldfirst@gmail.com commit -q -m "refresh <SGT>" && git push -q`. Done. No chat commentary beyond one status line.

Live (gated `wf`): https://socialworldfirst.github.io/afa-v2-live/
