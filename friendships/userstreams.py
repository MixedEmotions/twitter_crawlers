from xxx.twarc import Twarc
import sys
import os
import json
import time

client_key = ""
client_secret = ""
access_token = ""
access_token_secret = ""

def main():
	"""
	Main program
	"""
	# argument check
	if len(sys.argv) > 1:
		sys.stderr.write("ERROR\n")
		sys.exit(1)

	# check if data folder exists or create it
	if not os.path.isdir("data_user"):
		os.makedirs("data_user")

	# keep running stream function (every hour)
	while True:
		# call Twarc class
		t = Twarc(client_key, client_secret, access_token, access_token_secret)

		# call stream function every hour
		if stream(t) != True:
			sys.stderr.write("ERROR, STREAM QUITS\n")
			sys.exit(1)

def stream(t):
	"""
	Stream tweets from twitter and save them to file every hour

	Args:
		t - Twarc class

	Returns:
		boolean - True (OK) / False (Error)
	"""

	# make timestamp
	timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
	datestr = "data_user/"+time.strftime("%Y-%m-%d")

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
				for tweet in t.stream("followings"):
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
