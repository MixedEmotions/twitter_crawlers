from bottle import get, post, run
import os
import re
import time

server = "0.0.0.0"
port = 9081
file_server = "136.243.53.83"
port_file_server = 8001

def check_file_name(filename, start, end):
	# check format
	x = re.search("^\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d\.json$", filename)
	y = re.search("^\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d$", start)
	z = re.search("^\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d$", end)

	# if format is ok
	if x and y and z:
		# create time from strings
		file_time = int(time.mktime(time.strptime(filename.rsplit(".",1)[0], "%Y-%m-%d_%H-%M-%S")))
		start_time = int(time.mktime(time.strptime(start, "%Y-%m-%d_%H-%M-%S")))
		end_time = int(time.mktime(time.strptime(end, "%Y-%m-%d_%H-%M-%S")))
                now = time.time()
	        print("Filetime:%s, now:%s, diff:%s" % (file_time, now, now-file_time))
		if (int(time.time())-file_time) <= 3630:
			return False

		# check if file is in time interval
		if file_time > (start_time-3600) and file_time <= end_time:
			return True

        print("Not in the interval")
	return False

@get('/interval_all/<start>/<end>')
def do_intall(start, end):
	paths = []
	# go through files and directories
	for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(os.path.dirname(__file__))+"/data"):
		# for all files
		for filename in filenames:
                        print "Filename %s" % filename
			if check_file_name(filename, start, end):
				# adress of file
				path = "http://" + file_server + ":" + str(port_file_server) + "/" + os.path.basename(os.path.dirname(dirpath))+ "/" + os.path.basename(dirpath) + "/" + filename
				path = path.replace (" ", "_")
				paths.append(path)
	# return all adresses of files
	return ("<a href='%s'>%s</a><br/>" % (path, path) for path in paths)

@get('/interval_keyword/<keyword>/<start>/<end>')
def do_intkey(keyword, start, end):
	paths = []
	# go through files and directories
	for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(os.path.dirname(__file__))+"/data/"+keyword):
		# for all files
		for filename in filenames:
			if check_file_name(filename, start, end):
				# adress of file
				path = "http://" + file_server + ":" + str(port_file_server) + "/" + keyword + "/" + os.path.basename(dirpath) + "/" + filename
				path = path.replace (" ", "_")
				paths.append(path)
	# return all adresses of files
	return (path+"\n" for path in paths)

@get('/timestamp_all/<name>')
def do_timeall(name):
	paths = []
	# go through files and directories
	for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(os.path.dirname(__file__))+"/data"):
		# for all files
		for filename in filenames:
			if check_file_name(filename, name, time.strftime("%Y-%m-%d_%H-%M-%S")):
				# adress of file
				path = "http://" + file_server + ":" + str(port_file_server) + "/" + os.path.basename(os.path.dirname(dirpath)) + "/" + os.path.basename(dirpath) + "/" + filename
				path = path.replace (" ", "_")
				paths.append(path)
	# return all adresses of files
	return (path+"\n" for path in paths)

@get('/timestamp_keyword/<keyword>/<name>')
def do_timekey(keyword, name):
	paths = []
	# go through files and directories
	for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(os.path.dirname(__file__))+"/data/"+keyword):
		# for all files
		for filename in filenames:
			if check_file_name(filename, name, time.strftime("%Y-%m-%d_%H-%M-%S")):
				# adress of file
				path = "http://" + file_server + ":" + str(port_file_server) + "/" + keyword + "/" + os.path.basename(dirpath) + "/" + filename
				path = path.replace (" ", "_")
				paths.append(path)
	# return all adresses of files
	return (path+"\n" for path in paths)

# print keywords from file
@get('/print_keywords')
def do_print():
	with open("keywords.txt", "r") as f:
		file = f.read()
		f.close()
	return file

# add keyword to file	
@get('/add_keyword/<keyword>')
def do_add(keyword):
	keyword = keyword.replace("_", " ")
	count = 0
	with open("keywords.txt", "r+") as f:
		file = f.readlines()
		for line in file:
			if line.strip():
				count += 1
				line = line.rstrip('\n\t ')
				line = line.strip('\t ')
				# checking if key is in file 
				if line == keyword:
					return "Keyword is already in file.\n"
		if count >= 400:
			return "There is more than 400 keywords.\n" 

		f.write("\n%s" % keyword)
	return "Keyword was added successfully.\n"

# delete keyword from file  
@get('/delete_keyword/<keyword>')
def do_delete(keyword):
	keyword = keyword.replace("_", " ")
	new_file = ""
	with open("keywords.txt", "r") as f:
		file = f.readlines()
		f.close()
	for line in file:
		line = line.rstrip('\n\t ')
		line = line.strip('\t ')
		line = line.strip('\r')

		if line == keyword:
			continue
		else:
			new_file += line +"\n"

	new_file = new_file.rstrip('\n')
	with open("keywords.txt", "w") as f:
		f.write(new_file)
	return "Keyword was deleted successfully.\n"
# run api
run(host=server, port=port)
