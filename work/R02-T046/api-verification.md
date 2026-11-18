# API Verification & Availability Notes: Dictionaries (R02-T046)

## Selected Entries Probing Results

1. **Chinese Character Web**
   - URL: `http://ccdb.hemiola.com/`
   - Line in README: 901
   - Observed Status: HTTP 200 OK
   - Classification: `SUCCESS`
   - Assessment: Active and accessible.

2. **Chinese Text Project**
   - URL: `https://ctext.org/tools/api`
   - Line in README: 902
   - Observed Status: HTTP 200 OK
   - Classification: `SUCCESS`
   - Assessment: Active and accessible.

3. **Collins**
   - URL: `https://api.collinsdictionary.com/api/v1/documentation/html/`
   - Line in README: 903
   - Observed Status: HTTP 403 / Cloudflare Challenge (WAF managed challenge on automated curl/urllib clients).
   - Classification: `FORBIDDEN`
   - Assessment: Not a missing resource (not 404). Cloudflare protection / WAF response confirms the server and resource are live. Entry must remain in the catalogue.

## Policy Compliance
- No links were removed based on automated probe failures or 403 responses.
- Only confirmed 404 missing resources with manual verification can be proposed for removal.
