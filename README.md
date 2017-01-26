# twitter_crawlers
## About

MixedEmotions' Python service that connects to the Twitter streaming service and filters tweets with the related keywords.

This module includes three versions of the same basic functionality. The three versions are very similar. The basic differences are where they can read the data and where they can write the data.

These crawlers connect to the Twitter Stream API and listen for tweets. For each tweet they will verify if it contains the given conditions (match at least one synonym and no 'not') and if so, will save it.

* keyword crawler: Input are lines from a single file. It has a rest service to modify that data
* project crawler: Reads from projects.json the configuration of some "projects" to extract info from. Supports synonyms and forbidden words
* project crawler with hdfs: Same as before, but writes into HDFS.

## USAGE
For using these crawlers you will need to create a Twitter application and provide your tokens in the scripts. Edit the corresponding script and add your tokens in these lines:
```
  access_token = "Your tokens here"
  access_token_secret= ""
  client_key = ""
  client_secret = ""
  
  ```
  Regarding the projects crawler, first edit projects.json to add your project information data. Use the base `projects.json` file
```
  [
    {
        "name": "keyword1",
        "langs": ["en", "es"],
        "synonyms": ["synonym1", "synonym2 multiword allowed"],
        "nots": ["not1", "not2"],
        "id": 1
    },
    {
        "name": "keyword2",
        "langs": ["locale", "locale"],
        "synonyms": ["synonym1", "synonym2 multiword allowed"],
        "nots": ["not1", "not2"],
        "id": 2
    }
]
```
* name: project string identifier and synonym
* langs: allowed tweets declared languages
* synonyms: save tweets containing these phrases
* nots: among the tweets with the synonyms, discard tweets containing these phrases
* id: numerical id

Then execute `./start_project_twitter_crawler.sh`

Logs are saved in the `/logs` folder.


