# IPL Fantasy API

Some (mostly AI written) code to use the [cricketdata](https://cricketdata.org) API to fetch player scores for IPL matches, convert them with desired rules and then upload to a Google sheet. Scope to do lot more but leaving it as is for now.

To run: get google_credentials.json from a Google Project client account and an API key from cricketdata. Create congig.yaml with API_KEY and SHEET_ID and drop google json into parent folder. Run [sync_fantasy_points.py](sync_fantasy_points.py). For a new series simply fetch the seriesinfo.json for that series.