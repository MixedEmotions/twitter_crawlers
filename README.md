# twitter_crawlers
## About

MixedEmotions' Python service that connects to the Twitter streaming service and filters tweets with the related keywords.

This module includes three versions of the same basic functionality. The three versions are very similar. The basic differences are where they can read the data and where they can write the data.

These crawlers connect to the Twitter Stream API and listen for tweets. For each tweet they will verify if it contains the given conditions (match at least one synonym and no 'not') and if so, will save it.

* keyword crawler: Input are lines from a single file. It has a rest service to modify that data
* project crawler: Reads from projects.json the configuration of some "projects" to extract info from. Supports synonyms and forbidden words
* project crawler with hdfs: Same as before, but writes into HDFS.

## USAGE

For using these crawlers you will need to create a Twitter application and provide your tokens in the scripts.

### Projects Crawler

For using this crawler you will need to create a Twitter application and provide your tokens in the scripts. 

Edit `twitter_crawler_project.py`. Add your tokens in these lines:
```
  access_token = "Your tokens here"
  access_token_secret= ""
  client_key = ""
  client_secret = ""
  
  ```
  Also, change accepted languages, the streaming restarting time and the output directory in:
```
languages = ["es", "en"]

RESTART_TIME = 14400
PROJECTS_FOLDER = '/var/data/campaigns_twitter_crawler/collected_tweets/'
```

Take a look at `start_project_twitter_crawler.sh` and be sure pids and logs folder exist.
  
  
  
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

## Acknowledgement

This orchestrator was developed by [Paradigma Digital](https://en.paradigmadigital.com/) as part of the MixedEmotions project. This development has been partially funded by the European Union through the MixedEmotions Project (project number H2020 655632), as part of the `RIA ICT 15 Big data and Open Data Innovation and take-up` programme.

![MixedEmotions](https://raw.githubusercontent.com/MixedEmotions/MixedEmotions/master/img/me.png) 

![EU](https://raw.githubusercontent.com/MixedEmotions/MixedEmotions/master/img/H2020-Web.png)

 http://ec.europa.eu/research/participants/portal/desktop/en/opportunities/index.html
