import pickle
import re
import os
from collections import OrderedDict

from BeautifulSoup import BeautifulSoup
import random
import lxml.html

stopList = set(['and', 'is', 'it', 'an', 'as', 'are', 'have', 'in', 'their', 'said', 'from', 'for', 'also', 'by', 'to', 'other', 'which', 'new', 'has', 'was', 'more', 'be', 'we', 'that', 'but', 'they', 'not', 'with', 'than', 'a', 'on', 'these', 'of', 'could', 'this', 'so', 'can', 'at', 'the', 'or', 'first']) 

class Link:
  def __init__(self, url):
    self.url = url
    self.title = ""
    self.anchorText = []
  
  def __init__(self, url, title):
    self.url = url
    title = remove_stuff(title)
    self.title = title.encode('utf8')
    self.anchorText = set()

  def addTitle(self, title):
    self.title = title
  
  def addAnchorText(self, anchortext):
    if anchortext != "":
      anchortext = remove_stuff(anchortext)
      self.anchorText.add(anchortext.encode('utf8'))
    
  def setPageRank(self, pagerank):
    self.pagerank = pagerank
    
  def __str__(self):
    s = self.url + " " + str(self.pagerank) + " " + self.title + "\nAnchorText : "
    for anchor in self.anchorText:
      s = s + anchor + ", "
    return s    

urlDict = {}
postingList = {}

def loadUrlDict():
  global urlDict
  pkl_file = open('indexRecord.pkl', 'rb')
  urlDict = pickle.load(pkl_file)
  pkl_file.close()

def traverseUrlDict():
  for urlID in urlDict:
    l = urlDict[urlID]
    for word in l.title.split(" "):
      word = word.rstrip(",")
      if word in postingList:
        wordSet = postingList[word]
      else:
        wordSet = set()
      wordSet.add(urlID)
      
      postingList[word] = wordSet
      
    for word in l.anchorText:
      word = word.rstrip(",")
      if word in postingList:
        wordSet = postingList[word]
      else:
        wordSet = set()
      wordSet.add(urlID)
      
      postingList[word] = wordSet

def printUrlDict():
  for urlID in urlDict:
    print urlID, urlDict[urlID]

def remove_extra_spaces(data):
    'Function to remove extra white-spaces from text'
    p = re.compile(r'\s+')
    return p.sub(' ', data)    

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def searchQuery(term):
  if term in postingList and term not in stopList:
    pageSet = postingList[term]
    temp = {}
    for urlID in pageSet:
      l = urlDict[urlID]
      temp[urlID] = l.pagerank
    
    temp_sorted_by_value = OrderedDict(sorted(temp.items(), key=lambda x: x[1], reverse=True))
    for k, v in temp_sorted_by_value.items():
      print str(k) + " : ",
      filename = os.getcwd() + "/html/" + str(k+1) + ".html"
      f = open(filename, "r")
      html = f.read()
      f.close()
      soup = BeautifulSoup(html.lower())
      
      urlTitle = soup.find('title')
      try:
        urlTitleText = urlTitle.text
      except:
        try:
          t = lxml.html.parse(url)
          urlTitleText = t.find(".//title").text
        except:
          urlTitleText = ""
  
      print urlTitleText.lower(),
      body = soup.find("body")
      bodyList = body.text.split(" ")
      i = random.randint(0,len(bodyList))
      j = i + 10
      for term in bodyList[i:j]:
        term = remove_extra_spaces(term)
        term = remove_html_tags(term)
        if (re.match("\w",term)):
          print term,
        else:
          j = j + 1
      
      print
        
  else:
    if term in stopList:
      print "Searchterm is in stopList"
    else:
      print "Searchterm not found"
    
def main():
  loadUrlDict()
  #printUrlDict()
  traverseUrlDict()
  #print postingList

  while(1):
    searchTerm = raw_input("\nEnter search term : ")
    if len(searchTerm.split(" ")) == 1:
      searchTerm = searchTerm.lower()
      if re.match("zzz",searchTerm):
        print "Found ZZZ. Exiting"
        exit(0)
      
      searchQuery(searchTerm)
    else:
      print "Please enter a single search term"
  
if __name__ == "__main__":
    main()