
import sys
import os
import json
import time
import re
from datetime import datetime
from twarc import Twarc
from hdfs import InsecureClient


access_token = "put here your keys"
access_token_secret= ""
client_key = ""
client_secret = ""

total_keywords = {}

languages = ["es", "en"]

TWEET_DUMP_SIZE = 500
RESTART_TIME = 3600
HDFS_URL = 'http://192.168.1.2:50070'
HDFS_USER  = 'put here your hdfs_user'
PROJECTS_FOLDER = 'data/projects/'
WRITE_TO_FILE = False

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
            sys.stderr.write("ERROR, NEED VALID FILE\n")
            sys.exit(1)
    else:
        sys.stderr.write("ERROR, NEED FILE\n")
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

    hour_keywords = {}

    # make timestamps
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    datestr = time.strftime("%Y-%m-%d")

    # get total time for check time
    start_time = time.time()

    # create directories and files for keywords
    tweets_to_write = {}
    indexes = {}
    client = InsecureClient(HDFS_URL, user=HDFS_USER)
    for project in projects:
        project_id = project["id"]
        tweets_to_write[project_id] = []
        indexes[project_id] = 0

        if WRITE_TO_FILE:
            # for statistics
            if not os.path.isdir("data/statistics"):
                os.makedirs("data/statistics")

            # for statistics date
            if not os.path.isdir("data/statistics/"+datestr):
                os.makedirs("data/statistics/"+datestr)

            if not os.path.isdir("data/projects"):
                os.makedirs("data/projects")

            # for keyword
            if not os.path.isdir("data/projects/"+project_id):
                os.makedirs("data/projects/"+project_id)

            # for date
            if not os.path.isdir("data/projects/"+project_id+"/"+datestr):
                os.makedirs("data/projects/"+project_id+"/"+datestr)
            if not os.path.isdir("data/projects/"+project_id+"/"+datestr+"/twitter"):
                os.makedirs("data/projects/"+project_id+"/"+datestr+"/twitter")

            # create json file for writing data
            with open(filepath(project_id, datestr, timestr)+".json", "w") as fw:
                fw.write("[")

             

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
                    if tweet['lang'] in languages:
                        for keyword in project["synonyms"]:
                            # create list of words in keyword
                            wlist = keyword.split()
                            # length of this list
                            w_length = len(wlist)
                            # for every word in keyword
                            for w in wlist:
                                # check if word is in tweet
                                word_match = re.search("%s" % w, tweet["text"], re.IGNORECASE)
                                if word_match:
                                    check += 1
                                    if check== w_length:
                                        tweet["synonym_found"] = keyword
                                        is_tweet = True
                                        break
                            if len(wlist)==1:
                               word_match = re.search("@%s" % keyword, tweet["text"], re.IGNORECASE)
                               if word_match:
                                   tweet["synonym_found"] = "@%s" %  keyword
                                   is_tweet = True
                                   break
                            if is_tweet:
                                break 
                    # if every word from keyword is in tweet, save to file
                    if is_tweet:
                         print "%s - Tweet for %s" % (datetime.now(), project["name"])
                         tweets_to_write[project_id].append(tweet)
                         if WRITE_TO_FILE:
                             with open(filename + ".json", "a") as fw:
                                 dumped_json = json.dumps(tweet)
                                 fw.write(dumped_json)
                                 fw.write(",")

                         # counting total
                         if project_id in total_keywords:
                             total_keywords[project_id] += 1
                         else:
                             total_keywords[project_id] = 1
                         # counting hourly
                         if project_id in hour_keywords:
                             hour_keywords[project_id] += 1
                         else:
                             hour_keywords[project_id] = 1
                         
                         if len(tweets_to_write[project_id]) % TWEET_DUMP_SIZE == 0:
                             hdfs_write_tweets(tweets_to_write[project_id], filename+"_"+str(indexes[project_id]), project, client)
                             indexes[project_id] = indexes[project_id]+1
                             tweets_to_write[project_id] = []

                # exit every hour and start function again
                if start_time+RESTART_TIME < time.time():
                    print "An hour has passed, writing remaining tweets \n"
                    for project in projects:
                        project_id = project['id']
                        if WRITE_TO_FILE:
                            with open(filepath(project_id, datestr, timestr)+".json", "a+") as fw:
                                fw.seek(-1, os.SEEK_END)
                                if fw.read() == ",":
                                    fw.seek(-1, os.SEEK_END)
                                    fw.truncate()
                                fw.write("]")
                        print "%s - Remaining tweets to write %s: %s" % (datetime.now(), project_id, len(tweets_to_write[project_id]))
                        filename = filepath(project_id, datestr, timestr)
                        if(len(tweets_to_write[project_id])>0):
                            hdfs_write_tweets(tweets_to_write[project_id], filename+"_"+str(indexes[project_id]+1), project, client)
                    if WRITE_TO_FILE:
                        # hour statistics
                        with open("data/statistics"+"/"+datestr+"/"+timestr+".txt", "w") as fw:
                            for word in hour_keywords:
                                fw.write(str(word) + " : " + str(hour_keywords[word]) + "\n")
                        # total statistics
                        with open("data/statistics/statistics.txt", "w") as fw:
                            for word in total_keywords:
                                fw.write(str(word) + " : " + str(total_keywords[word]) + "\n")
                    return True

        # except for quit application
        except KeyboardInterrupt:
            for project in projects:
                word = project["name"]
                project_id = project['id']
                if WRITE_TO_FILE:
                    with open(filepath(project_id, datestr, timestr)+".json", "a+") as fw:
                        fw.seek(-1, os.SEEK_END)
                        if fw.read() == ",":
                            fw.seek(-1, os.SEEK_END)
                            fw.truncate()
                        fw.write("]")
            if WRITE_TO_FILE:
                # hour statistics
                with open("data/statistics"+"/"+datestr+"/"+timestr+".txt", "w") as fw:
                    for word in hour_keywords:
                        fw.write(str(word) + " : " + str(hour_keywords[word]) + "\n")
                # total statistics
                with open("data/statistics/statistics.txt", "w") as fw:
                    for word in total_keywords:
                        fw.write(str(word) + " : " + str(total_keywords[word]) + "\n")
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


def hdfs_write_tweets(tweets_to_write, filename, project, client):
    print "Going to write %s into %s" % (len(tweets_to_write), filename)
    formatted_tweets = [format_tweet(tweet,project) for tweet in tweets_to_write]
    text_to_write = "\n".join(formatted_tweets)
    with client.write(filename, encoding='utf-8') as writer:
        writer.write(text_to_write)

def filepath(project_id, datestr, timestr):
    return PROJECTS_FOLDER+str(project_id)+"/"+datestr+"/twitter/"+timestr

def parse_twitter_time(twitter_time):
    twitter_time = re.sub("[\-\+]\d\d\d\d ", "", twitter_time)
    date = datetime.strptime(twitter_time, "%a %b %d %H:%M:%S %Y")
    return date.strftime("%Y%m%d%H%M%S")


if __name__ == "__main__":
    main()
