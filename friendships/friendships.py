from twarc import Twarc
import tweepy
import sys
import os
import json
import time

twarc_client_key = ""
twarc_client_secret = ""
twarc_access_token = ""
twarc_access_token_secret = ""

tweepy_client_key = ""
tweepy_client_secret = ""
tweepy_access_token = ""
tweepy_access_token_secret = ""

limit =

friends = {}

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

	# array of streaming words
	keys = ""

	# open file for read
	with open(input_file, "r") as fr:
		for line in fr:
			# empty line
			if line != '\n':
				# remove white chars in start and end of line
				line = line.rstrip('\n\t ')
				line = line.strip('\t ')
				# append line to array
				keys = keys + line + ","

	keys = keys.rstrip(",")

	# check if data folder exists or create it
	if not os.path.isdir("data"):
		os.makedirs("data")

	# keep running stream function (every hour)
	while True:
		# create Twarc class
		t = Twarc(twarc_client_key, twarc_client_secret, twarc_access_token, twarc_access_token_secret)
		
		# create tweepy connection
		auth = tweepy.OAuthHandler(tweepy_client_key, tweepy_client_secret)
		auth.set_access_token(tweepy_access_token, tweepy_access_token_secret)

		# create tweepy class
		api = tweepy.API(auth)

		# call stream function every hour
		if stream(keys, t) != True:
			sys.stderr.write("ERROR, STREAM QUITS\n")
			sys.exit(1)

		# get friends list
		ids = api.friends_ids("knot_group")
		# get ids of users
		f_keys = friends.keys()
		# for every user
		for f_key in f_keys:
			# get value
			value = friends.get(f_key)
			if value >= limit:
				# user not in friend list
				if not f_key in ids:
					# create friendship
					api.create_friendship(f_key)

def stream(lines, t):
	"""
	Stream tweets from twitter and save them to file every hour

	Args:
		lines - array of streaming words
		t - Twarc class

	Returns:
		boolean - True (OK) / False (Error)
	"""
	words = lines

	# make timestamp
	timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
	datestr = "data/"+time.strftime("%Y-%m-%d")

	# get total time for chceck time
	start_time = time.time()

	# check if folder of day exists in data folder or create it
	if not os.path.isdir(datestr):
		os.makedirs(datestr)

	# open file for write
	with open(datestr+"/"+timestr+".json", "w") as fw:
		fw.write("[")
		while True:
			try:
				# find lines in twiiter
				for tweet in t.stream(words):
					# user already in dictionary gets +1 to count
					if tweet["user"]["id"] in friends:
						friends[tweet["user"]["id"]] += 1
					# user not in dictionary is added with count 1
					else:
						friends[tweet["user"]["id"]] = 1
					# print found tweet
					fw.write(json.dumps(tweet))
					# exit every hour and start function again for new file
					if start_time+3600 < time.time():
						fw.write("]")
						return True
					fw.write(",")

			# except for quit application
			except KeyboardInterrupt:
				fw.write("]")
				sys.stdout.write("QUIT\n")
				sys.exit(0)
			except KeyError:
				continue
	# error
	return False

if __name__ == "__main__":
	main()
