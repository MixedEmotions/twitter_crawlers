
import sys
import os
import json
import time
import re
from datetime import datetime
from twarc import Twarc


access_token = "Your tokens here"
access_token_secret= ""
client_key = ""
client_secret = ""

total_keywords = {}

languages = ["es", "en"]

RESTART_TIME = 14400
PROJECTS_FOLDER = '/var/data/inputs/projects/'

def main():
    """
    Main program
    """
    # argument check
    if len(sys.argv) > 1:
        # if argument file exists
        if os.access(sys.argv[1], os.R_OK):
            input_file = sys.argv[1]
        else:
            sys.stderr.write("ERROR, NEED VALID PROJECT FILE!\n")
            sys.stderr.write("%s NOT ACCESSIBLE!\n"%sys.argv[1])
            sys.exit(1)
    else:
        sys.stderr.write("ERROR, NEED PROJECT FILE\n")
        sys.exit(1)

    # check if data folder exists or create it
    if not os.path.isdir("data"):
        os.makedirs("data")

    # keep running stream function (every hour)
    while True:

        # string of streaming words
        print "Starting"
        keys = ""
        lines = []
        projects = []

        # open file for read
        with open(input_file, "r") as fr:
            string_txt = fr.read()
            projects = json.loads(string_txt)
        for project in projects:
            keys += ",".join(project["synonyms"]) + ","

        print("Projects %s" % str(projects))
        keys = keys.rstrip(",")

        # create Twarc class
        t = Twarc(client_key, client_secret, access_token, access_token_secret)

        # call stream function every hour
        if stream(keys, projects, t) != True:
            sys.stderr.write("ERROR, STREAM QUITS\n")
            sys.exit(1)

def stream(query, projects, t):
    """
    Stream tweets from twitter and save them to file every hour

    Args:
        lines - array of streaming words
        t - Twarc class

    Returns:
        boolean - True (OK) / False (Error)
    """
    # make timestamps
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    datestr = time.strftime("%Y-%m-%d")

    # get total time for check time
    start_time = time.time()

    # create directories and files for keywords
    for project in projects:
        project_id = project["id"]
        #Creating folders
        if not os.path.isdir(PROJECTS_FOLDER + "projects"):
            os.makedirs(PROJECTS_FOLDER + "projects")

        # for keyword
        if not os.path.isdir(PROJECTS_FOLDER + "/%s" % datestr):
            os.makedirs(PROJECTS_FOLDER + "/%s" % datestr)

        # for date
        if not os.path.isdir(PROJECTS_FOLDER + "/%s/%s" % (datestr, project_id)):
            os.makedirs(PROJECTS_FOLDER + "/%s/%s" % (datestr, project_id))
        if not os.path.isdir(PROJECTS_FOLDER + "/%s/%s/twitter" % (datestr, project_id)):
            os.makedirs(PROJECTS_FOLDER + "/%s/%s/twitter" % (datestr, project_id))

        ## create json file for writing data
        #with open(filepath(project_id, datestr, timestr)+".json", "w") as fw:
        #    #fw.write("[")
        #    fw.write("")

             

    while True:
        try:
            # find lines in twitter
            print "Query string: %s" % query 
            for tweet in t.stream(query):
                # regex to find keyword
                for project in projects:
                    project_id = project["id"]
                    filename = filepath(project_id, datestr, timestr)
                    check = 0
                    is_tweet = False
                    if 'lang' in tweet.keys() and tweet['lang'] in languages:
                        for keyword in project["synonyms"]:
                            # create list of words in keyword
                            wlist = keyword.split()
                            # length of this list
                            w_length = len(wlist)
                            # for every word in keyword
                            for w in wlist:
                                # check if word is in tweet
                                word_match = re.search(r"\b%s\b" % w, tweet["text"], re.IGNORECASE)
                                if word_match:
                                    check += 1
                                    if check== w_length:
                                        tweet["synonym_found"] = keyword
                                        is_tweet = True
                                        break
                            if len(wlist)==1:
                               word_match = re.search(r"@%s\b" % keyword, tweet["text"], re.IGNORECASE)
                               if word_match:
                                   tweet["synonym_found"] = "@%s" %  keyword
                                   is_tweet = True
                                   break
                            if is_tweet:
                                break 
                    # if every word from keyword is in tweet, save to file
                    if is_tweet:
                         if has_not_words(tweet["text"],project["nots"]):
                             #print "Has not words: '%s' in '%s'" % (project["nots"], tweet["text"])
                             print "Has not words "
                             continue
                         print "%s - Tweet for %s" % (datetime.now(), project["name"])
                         stop=False
                         if(tweet['geo']!=None):
                             print "Inverting geo"
                             (lat,lon) = tweet['geo']['coordinates']
                             tweet['geo']['coordinates'] = [lon, lat]
                         with open(filename + ".txt", "a") as fw:
                             tweet['project_id'] = project_id
                             tweet['project_name'] = project['name']
                             dumped_json = json.dumps(tweet)
                             fw.write(dumped_json)
                             fw.write("\n")
                # exit every hour and start function again
                if start_time+RESTART_TIME < time.time():
                    return True

        # except for quit application
        except KeyboardInterrupt:
            sys.stdout.write("QUIT\n")
            sys.exit(0)
    return False

def format_tweet(tweet, project):
    structure = {"source":"twitter",
                 "brand": project["name"],
                 "synonym_found": tweet["synonym_found"],
                 "synonyms": project["synonyms"],
                 "nots": project["nots"],
                 "project_id": project["id"],
                 "raw": tweet,
                 "text": tweet["text"],
                 "time": parse_twitter_time(tweet["created_at"]),
                 "url": "http://twitter.com/statuses/%s" % tweet["id_str"],
                 "lang": tweet["lang"]
                }
    return json.dumps(structure)



def filepath(project_id, datestr, timestr):
    #return PROJECTS_FOLDER+str(project_id)+"/"+datestr+"/twitter/"+timestr
    return PROJECTS_FOLDER+datestr+"/"+str(project_id)+"/twitter/"+timestr

def parse_twitter_time(twitter_time):
    twitter_time = re.sub("[\-\+]\d\d\d\d ", "", twitter_time)
    date = datetime.strptime(twitter_time, "%a %b %d %H:%M:%S %Y")
    return date.strftime("%Y%m%d%H%M%S")

def has_not_words(text, nots_array):
    for not_phrase in nots_array:
        match = re.search(not_phrase,  text, re.IGNORECASE)
        if match:
           return True
    return False

if __name__ == "__main__":
    main()
