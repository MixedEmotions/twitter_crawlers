from twarc import Twarc
from hdfs import InsecureClient

import sys
import os
import json
import time
import re

access_token = "put here your tokens"
access_token_secret= ""
client_key = ""
client_secret = ""

total_keywords = {}

languages = ["es", "en"]

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
		keys = ""
		lines = []

		# open file for read
		with open(input_file, "r") as fr:
			for line in fr:
				# empty line
				if line != '\n':
					# remove white chars in start and end of line
					line = line.rstrip('\n\t ')
					line = line.strip('\t ')
					# append line to array and string
					keys = keys + line + ","
					lines.append(line)

		keys = keys.rstrip(",")

		# create Twarc class
		t = Twarc(client_key, client_secret, access_token, access_token_secret)

		# call stream function every hour
		if stream(keys, lines, t) != True:
			sys.stderr.write("ERROR, STREAM QUITS\n")
			sys.exit(1)

def stream(string, lines, t):
	"""
	Stream tweets from twitter and save them to file every hour

	Args:
		lines - array of streaming words
		t - Twarc class

	Returns:
		boolean - True (OK) / False (Error)
	"""
	words = lines
	string = string

	hour_keywords = {}

	# make timestamps
	timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
	datestr = time.strftime("%Y-%m-%d")

	# get total time for check time
	start_time = time.time()

	# create directories and files for keywords
        tweets_to_write = {}
        indexes = {}
        client = InsecureClient('http://192.168.1.12:50070', user='stratio')
	for word in words:
		dir_word = word.replace(" ", "_")

		# for statistics
		if not os.path.isdir("data/statistics"):
			os.makedirs("data/statistics")

		# for statistics date
		if not os.path.isdir("data/statistics/"+datestr):
			os.makedirs("data/statistics/"+datestr)

		# for keyword
		if not os.path.isdir("data/"+dir_word):
			os.makedirs("data/"+dir_word)

		# for date
		if not os.path.isdir("data/"+dir_word+"/"+datestr):
			os.makedirs("data/"+dir_word+"/"+datestr)

		# create json file for writing data
		with open("data/"+dir_word+"/"+datestr+"/"+timestr+".json", "w") as fw:
			fw.write("[")

                tweets_to_write[dir_word] = []
                indexes[dir_word] = 0
             

        minutes = 1
	while True:
		try:
			# find lines in twitter
                        print "String query: %s" % string 
			for tweet in t.stream(string):
				# regex to find keyword
				for word in words:
					dir_word = word.replace(" ", "_")
                			filename = "data/"+dir_word+"/"+datestr+"/"+timestr
					# create list of words in keyword
					wlist = word.split()
					# length of this list
					w_length = len(wlist)
					check = 0
					# for every word in keyword
					for w in wlist:
						# check if word is in tweet
						keyword = re.search("%s" % w, tweet["text"], re.IGNORECASE)
						if keyword:
							check += 1
					# if every word from keyword is in tweet, save to file
					if check == w_length:
                                                print "Tweet language: %s" % tweet['lang']
                                                if tweet['lang'] in languages:
                                                	dumped_json = json.dumps(tweet)
                                                        tweets_to_write[dir_word].append(dumped_json)
							with open(filename + ".json", "a") as fw:
                                                	    
								fw.write(dumped_json)
								fw.write(",")
                                                	 
                                	        	


							# counting total
							if word in total_keywords:
								total_keywords[word] += 1
							else:
								total_keywords[word] = 1
							# counting hourly
							if word in hour_keywords:
								hour_keywords[word] += 1
							else:
								hour_keywords[word] = 1
                                                        if len(tweets_to_write[dir_word]) % 10 == 0:
                                            			print "Goint to write into %s_%s" % (filename, indexes[dir_word])
                                	    			with client.write(filename + "_" + str(indexes[dir_word]), encoding='utf-8') as writer:
                                	    			    writer.write("\n".join(tweets_to_write))
                                	    			indexes[dir_word] = indexes[dir_word]+1
                                	    			tweets_to_write[dir_word] = []

				# exit every hour and start function again
				if start_time+3600 < time.time():
					for word in words:
						dir_word = word.replace(" ", "_")
						with open("data/"+dir_word+"/"+datestr+"/"+timestr+".json", "a+") as fw:
							fw.seek(-1, os.SEEK_END)
							if fw.read() == ",":
								fw.seek(-1, os.SEEK_END)
								fw.truncate()
							fw.write("]")
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
			for word in words:
				dir_word = word.replace(" ", "_")
				with open("data/"+dir_word+"/"+datestr+"/"+timestr+".json", "a+") as fw:
					fw.seek(-1, os.SEEK_END)
					if fw.read() == ",":
						fw.seek(-1, os.SEEK_END)
						fw.truncate()
					fw.write("]")
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
		# except for problems with key
		except KeyError:
			# exit every hour and start function again
			if start_time+3600 < time.time():
				for word in words:
					dir_word = word.replace(" ", "_")
					with open("data/"+dir_word+"/"+datestr+"/"+timestr+".json", "a+") as fw:
						fw.seek(-1, os.SEEK_END)
						if fw.read() == ",":
							fw.seek(-1, os.SEEK_END)
							fw.truncate()
						fw.write("]")
				# hour statistics
				with open("data/statistics"+"/"+datestr+"/"+timestr+".txt", "w") as fw:
					for word in hour_keywords:
						fw.write(str(word) + " : " + str(hour_keywords[word]) + "\n")
				# total statistics
				with open("data/statistics/statistics.txt", "w") as fw:
					for word in total_keywords:
						fw.write(str(word) + " : " + str(total_keywords[word]) + "\n")
				return True
			continue
	# error
	return False

if __name__ == "__main__":
	main()
