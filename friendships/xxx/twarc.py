#!/usr/bin/env python

from __future__ import print_function

import io
import os
import sys
import json
import time
import logging
import argparse
import requests

from requests_oauthlib import OAuth1Session

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
else:
    # Python 3
    get_input = input


def main():
    """
    The twarc command line.
    """
    parser = argparse.ArgumentParser("twarc")
    parser.add_argument("--search", dest="search",
                        help="search for tweets matching a query")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum tweet id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--stream", dest="stream",
                        help="stream tweets matching filter")
    parser.add_argument("--hydrate", dest="hydrate",
                        help="rehydrate tweets from a file of tweet ids")
    parser.add_argument("--log", dest="log",
                        default="twarc.log", help="log file")
    parser.add_argument("--consumer_key",
                        default=None, help="Twitter API consumer key")
    parser.add_argument("--consumer_secret",
                        default=None, help="Twitter API consumer secret")
    parser.add_argument("--access_token",
                        default=None, help="Twitter API access key")
    parser.add_argument("--access_token_secret",
                        default=None, help="Twitter API access token secret")
    parser.add_argument('-c', '--config',
                        default=default_config_filename(),
                        help="Config file containing Twitter keys and secrets")
    parser.add_argument('-p', '--profile', default='main',
                        help="Name of a profile in your configuration file")
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    consumer_key = args.consumer_key or os.environ.get('CONSUMER_KEY')
    consumer_secret = args.consumer_secret or os.environ.get('CONSUMER_SECRET')
    access_token = args.access_token or os.environ.get('ACCESS_TOKEN')
    access_token_secret = args.access_token_secret or os.environ.get("ACCESS_TOKEN_SECRET")

    if not (consumer_key and consumer_secret and
            access_token and access_token_secret):
        credentials = load_config(args.config, args.profile)
        if credentials:
            consumer_key = credentials['consumer_key']
            consumer_secret = credentials['consumer_secret']
            access_token = credentials['access_token']
            access_token_secret = credentials['access_token_secret']
        else:
            print("Please enter Twitter authentication credentials")
            consumer_key = get_input('consumer key: ')
            consumer_secret = get_input('consumer secret: ')
            access_token = get_input('access_token: ')
            access_token_secret = get_input('access token secret: ')
            save_keys(args.profile, consumer_key, consumer_secret,
                      access_token, access_token_secret)

    t = Twarc(consumer_key=consumer_key,
              consumer_secret=consumer_secret,
              access_token=access_token,
              access_token_secret=access_token_secret)

    if args.search:
        tweets = t.search(
            args.search,
            since_id=args.since_id,
            max_id=args.max_id
        )
    elif args.stream:
        tweets = t.stream(args.stream)
    elif args.hydrate:
        tweets = t.hydrate(open(args.hydrate, 'rU'))
    else:
        raise argparse.ArgumentTypeError(
            "must supply one of: --search --stream or --hydrate")

    # iterate through the tweets and write them to stdout
    for tweet in tweets:
        if "id_str" in tweet:
            logging.info("archived %s", tweet["id_str"])
            print(json.dumps(tweet))


def load_config(filename, profile):
    if not os.path.isfile(filename):
        return None
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in ['access_token', 'access_token_secret', 'consumer_key', 'consumer_secret']:
        try:
            data[key] = config.get(profile, key)
        except configparser.NoSectionError:
            sys.exit("no such profile %s in %s" % (profile, filename))
        except configparser.NoOptionError:
            sys.exit("missing %s from profile %s in %s" % (key, profile, filename))
    return data


def save_config(filename, profile,
                consumer_key, consumer_secret,
                access_token, access_token_secret):
    config = configparser.ConfigParser()
    config.add_section(profile)
    config.set(profile, 'consumer_key', consumer_key)
    config.set(profile, 'consumer_secret', consumer_secret)
    config.set(profile, 'access_token', access_token)
    config.set(profile, 'access_token_secret', access_token_secret)
    with open(filename, 'w') as config_file:
        config.write(config_file)


def default_config_filename():
    """
    Return the default filename for storing Twitter keys.
    """
    home = os.path.expanduser("~")
    return os.path.join(home, ".twarc")


def save_keys(profile, consumer_key, consumer_secret,
              access_token, access_token_secret):
    """
    Save keys to ~/.twarc
    """
    filename = default_config_filename()
    save_config(filename, profile,
                consumer_key, consumer_secret,
                access_token, access_token_secret)
    print("Keys saved to", filename)


def rate_limit(f):
    """
    A decorator to handle rate limiting from the Twitter API. If
    a rate limit error is encountered we will sleep until we can
    issue the API call again.
    """
    def new_f(*args, **kwargs):
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                reset = int(resp.headers['x-rate-limit-reset'])
                now = time.time()
                seconds = reset - now + 10
                if seconds < 1:
                    seconds = 10
                logging.warn("rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            elif resp.status_code == 503:
                seconds = 60
                logging.warn("503 from Twitter API, sleeping %s", seconds)
                time.sleep(seconds)
            else:
                resp.raise_for_status()
    return new_f


class Twarc(object):
    """
    Your friendly neighborhood Twitter archiving class. Twarc allows
    you to search for existing tweets, stream live tweets that match
    a filter query and lookup (hdyrate) a list of tweet ids.

    Each method search, stream and hydrate returns a tweet iterator which
    allows you to do what you want with the data. Twarc handles rate limiting
    in the API, so it will go to sleep when Twitter tells it to, and wake back
    up when it is able to get more data from the API.
    """

    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret):
        """
        Instantiate a Twarc instance. Make sure your environment variables
        are set.
        """

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self._connect()

    def search(self, q, max_id=None, since_id=None):
        """
        Pass in a query with optional max_id and min_id and get back
        an iterator for decoded tweets.
        """
        logging.info("starting search for %s", q)
        url = "https://api.twitter.com/1.1/search/tweets.json"
        params = {
            "count": 100,
            "q": q
        }

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id

            resp = self.get(url, params=params)
            statuses = resp.json()["statuses"]

            if len(statuses) == 0:
                logging.info("no new tweets matching %s", params)
                break

            for status in statuses:
                yield status

            max_id = str(int(status["id_str"]) - 1)

    def stream(self, query):
        """
        Returns an iterator for tweets that match a given filter query from
        the livestream of tweets happening right now.
        """
        url = 'https://userstream.twitter.com/1.1/user.json'
        params = {"with":"followings"}
        headers = {'accept-encoding': 'deflate, gzip'}
        errors = 0
        while True:
            try:
                logging.info("connecting to filter stream for %s", query)
                resp = self.post(url, params, headers=headers, stream=True)
                errors = 0
                for line in resp.iter_lines(chunk_size=512):
                    if line == "": 
                        logging.info("keep-alive")
                        continue
                    try:
                        yield json.loads(line.decode())
                    except Exception as e:
                        logging.error("json parse error: %s - %s", e, line)
            except requests.exceptions.HTTPError as e:
                errors += 1
                logging.error(e)
                if e.response.status_code == 420:
                    t = errors * 60
                    logging.info("sleeping %s", t)
                    time.sleep(t)
                else:
                    t = errors * 5
                    logging.info("sleeping %s", t)
                    time.sleep(t)
            except Exception as e:
                errors += 1
                t = errors * 1
                logging.error(e)
                logging.info("sleeping %s", t)
                time.sleep(t)

    def hydrate(self, iterator):
        """
        Pass in an iterator of tweet ids and get back an iterator for the
        decoded JSON for each corresponding tweet.
        """
        ids = []
        url = "https://api.twitter.com/1.1/statuses/lookup.json"

        # lookup 100 tweets at a time
        for tweet_id in iterator:
            tweet_id = tweet_id.strip()  # remove new line if present
            ids.append(tweet_id)
            if len(ids) == 100:
                logging.info("hydrating %s ids", len(ids))
                resp = self.post(url, data={"id": ','.join(ids)})
                tweets = resp.json()
                tweets.sort(key=lambda t: t['id_str'])
                for tweet in tweets:
                    yield tweet
                ids = []

        # hydrate any remaining ones
        if len(ids) > 0:
            logging.info("hydrating %s", ids)
            resp = self.client.post(url, data={"id": ','.join(ids)})
            for tweet in resp.json():
                yield tweet

    @rate_limit
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    @rate_limit
    def post(self, *args, **kwargs):
        try:
            return self.client.post(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.post(*args, **kwargs)

    def _connect(self):
        logging.info("creating http session")
        self.client = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )

if __name__ == "__main__":
    main()
