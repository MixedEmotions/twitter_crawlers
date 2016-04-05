from twarc import Twarc
import sys
import os
import json
import time

client_key = ""
client_secret = ""
access_token = ""
access_token_secret = ""

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

	# string of streaming words
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
		t = Twarc(client_key, client_secret, access_token, access_token_secret)

		# call stream function every hour
		if stream(keys, t) != True:
			sys.stderr.write("ERROR, STREAM QUITS\n")
			sys.exit(1)

		# open file for statistics of user tweets
		with open("data/statistics.txt", "w") as fs:
			# write user's id + number of tweets to file
			for key, value in sorted(friends.iteritems(), key=lambda (k,v): (v,k), reverse=True):
				fs.write(str(key) + " : " + str(value) + "\n")

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
					# write found tweet
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
