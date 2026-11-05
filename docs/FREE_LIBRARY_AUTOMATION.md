# Free SFX → GitHub Pages daily publishing (v1)

## Status

- PRIVATE audio producer: `bulmue-dot/lokal-audio-lab`
  - Runs at 09:00 WIB (best-effort GitHub Actions cron).
  - Produces 10 private candidates, technical QC and Signal Listener evaluation.
  - Explicitly selects **up to 3** zero-flag, eligible sounds as `FREE_DEMO`.
  - Adds `free-demo-catalog.json` and `free-demo-pack.zip` to private SFX Release.
  - Premium master bundle, QC reports, and Google Drive REVIEW_CANDIDATES stay private.
- PUBLIC website: `lokalaudiolab/lokalaudiolab.github.io`
  - Refresh scheduled 12:30 WIB via `daily-free-library.yml`.
  - Imports free-only asset files, validating ZIP contents, SHA256, filenames and metadata.
  - Appends public WAVs and a cumulative `library/catalog.json`.
  - Commits public data to `main` with `GITHUB_TOKEN`.
  - **Explicitly deploys** GitHub Pages artifact with `actions/deploy-pages`, since
    `GITHUB_TOKEN` pushes alone do not start branch-based Pages builds.
  - Page shows fresh/free WAVs with play, search, category filter and download.
  - Six original in-browser demos remain available if the daily sync fails.

## ONE-TIME AUTHORIZATION REQUIRED

The GitHub Actions `GITHUB_TOKEN` inside a public website repo cannot read
a separate **private** producer repository. A fine-grained read-only token
is necessary. Never put it in commits, README, browser HTML, screenshots
or messages to ChatGPT.

### Create the minimal source token

1. Visit https://github.com/settings/personal-access-tokens/new
2. Token name: `LAL Free SFX Source Reader`
3. Resource owner: **bulmue-dot** (personal account with the private producer repo).
4. Expiration: choose an expiry policy and calendar an alert for rotation.
5. Repository access: **Only select repositories** → `lokal-audio-lab`.
6. Repository permissions: **Contents: Read-only** (Metadata: Read automatically).
7. Generate token and copy it once; do not share it.

### Store on the website ONLY

1. Visit https://github.com/lokalaudiolab/lokalaudiolab.github.io/settings/secrets/actions
2. New repository secret:
   - Name: `SFX_SOURCE_READ_TOKEN`
   - Value: the **private** token created above.
3. Click Add secret.

### Confirm one successful sync

1. Visit https://github.com/lokalaudiolab/lokalaudiolab.github.io/actions/workflows/daily-free-library.yml
2. Click **Run workflow** on **main**.
3. Check the `Import new private-producer FREE packs only` and `Deploy site and audio together` steps.
4. Verify https://lokalaudiolab.github.io/#dailyFreeSection
5. Under the website repo, inspect `library/catalog.json` and `library/audio`.
   No premium master archives should appear.

## Safeguards / limitations

- No credential or private Google Drive endpoint in public source.
- Uploads are from a private Release with explicit `FREE_DEMO` metadata.
- Zero-flag selection is **not trained audio-perception or human creative approval**;
  this is a transparently labelled experimental free-demo policy.
- If a day's 10 candidates yield no technically eligible free tracks, the library
  retains older drops and **does not publish questionable audio**.
- GitHub schedule is best-effort; runs may be delayed or skipped.
- Existing WAVs are never silently overwritten or deleted. Import is idempotent.
- Website GitHub Pages size limit is 1 GB; importer blocks above ~800 MB,
  and a long-term object-storage plan will eventually be needed.
- If the private token expires or loses access, refresh it in repository Secrets.
- For commercial *premium* licensing, add separate legal/product vetting.
- Note: only free copies are made public; new MP3 preview conversion is not
  included (WAV PCM16 mono 48 kHz).

References:
- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
