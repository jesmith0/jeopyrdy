from bs4 import BeautifulSoup
import re
import urllib2
import os


def __get_soup(url,header):
	return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)), "html5lib")

def search(query):
	image_type = "Action"
	# you can change the query for the image  here  
	#query = "felipe esparza"
	#query= query.split()
	#query='+'.join(query)
	url="https://www.google.co.in/search?q="+('+'.join(query.split()))+"&source=lnms&tbm=isch"
	print url
	header = {'User-Agent': 'Mozilla/5.0'}
	#header = {}
	print urllib2.Request(url,headers=header)
	print urllib2.urlopen(urllib2.Request(url,headers=header))
	soup = __get_soup(url,header)

	print soup

	images = [a['src'] for a in soup.find_all("img", {"src": re.compile("gstatic.com")})]

	DIR = os.getcwd() + "\\temp\\"
	print DIR

	raw_img = urllib2.urlopen(images[0]).read()
	#add the directory for your image here 
	cntr = len([i for i in os.listdir(DIR) if image_type in i]) + 1

	path = DIR + image_type + "_"+ str(cntr)+".jpg"

	f = open(path, 'wb')
	f.write(raw_img)
	f.close()

	return path
