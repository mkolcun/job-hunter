---
name: consolidate
description: Consolidate all scraping sessions and remove duplicates
---

# Consolidate Jobs

Run the consolidator skill to:
1. Find all session directories
2. Load jobs from each session
3. Detect and remove duplicates
4. Save unified database

Use the **consolidator** skill.

After consolidation completes, show user:
- Total sessions found
- Total jobs scraped
- Unique jobs
- Duplicate rate
- File locations
