# Download files and extract links to make a vector
from __future__ import division
import re
import urllib
from urlparse import urljoin
import pickle
from htmlentitydefs import name2codepoint as n2cp

from BeautifulSoup import BeautifulSoup
import lxml.html
import numpy


urlDict = {}
urlUrlIDPair = {}
stopList = set(['and', 'is', 'it', 'an', 'as', 'are', 'have', 'in', 'their', 'said', 'from', 'for', 'also', 'by', 'to', 'other', 'which', 'new', 'has', 'was', 'more', 'be', 'we', 'that', 'but', 'they', 'not', 'with', 'than', 'a', 'on', 'these', 'of', 'could', 'this', 'so', 'can', 'at', 'the', 'or', 'first']) 

def remove_html_tags(data):
    'Function to remove html tags from text'
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def remove_extra_spaces(data):
    'Function to remove extra white-spaces from text'
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def remove_html_entities(string):
    'Function to remove extra html-entity from text'
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

    def substitute_entity(match):
        ent = match.group(2)
        if match.group(1) == "#":
            return unichr(int(ent))
        else:
            cp = n2cp.get(ent)

            if cp:
                return unichr(cp)
            else:
                return match.group()

    return entity_re.subn(substitute_entity, string)[0]

def remove_stuff(data):
    data = remove_html_tags(data)
    data = remove_extra_spaces(data)
    data = remove_html_entities(data)
    return data 

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

def traverseURLSet():
  matrix = numpy.zeros(shape=(len(urlDict),len(urlDict)))
  for urlID in urlDict:
    l = urlDict[urlID]
    response = urllib.urlopen(l.url)
    html = response.read()
    html = html.replace(r'\"', '"')
    soup = BeautifulSoup(html.lower())
    alinks = soup.findAll('a')
    
    if alinks:
      for alink in alinks:
        
        try:
          hrefFound = alink['href']
        except:
          hrefFound = ""
          
        if(re.match("mail",hrefFound)):
          continue
        
        if(re.search("#",hrefFound)):
          hrefFound = hrefFound.split("#")[0]
        
        if hrefFound.rstrip("/") == hrefFound:
          if hrefFound != "" and not re.search("html$",hrefFound) and not re.search("htm$",hrefFound) and not re.search("css$",hrefFound):
            hrefFound =  hrefFound + "/"
      
        urlFound = urljoin(l.url, hrefFound)
       
        if(re.search("#",urlFound)):
          urlFound = urlFound.split("#")[0]
        
        if urlFound in urlUrlIDPair:
          print alink, urlFound
          row = urlUrlIDPair[l.url]
          col = urlUrlIDPair[urlFound]
          matrix[row][col]=1
          
          try:
            alinkText = alink.text
          except:
            alinkText = ""
              
          urlID = urlUrlIDPair[urlFound]
          l1 = urlDict[urlID]
          
          print l.url
          print urlFound
          print alinkText
          
          l1.addAnchorText(alinkText)
          
          try:
            alinksoup = BeautifulSoup(str(alink))
            img = alinksoup.find('img')
            alinkText = img['alt']
          except:
            alinkText = ""
          
          l1.addAnchorText(alinkText)
        
    else:
      print "No links found in", l.url
    
  return matrix

def getTitle(url):
  response = urllib.urlopen(url)
  html = response.read()
  html = html.replace(r'\"', '"')
  soup = BeautifulSoup(html.lower())
  urlTitle = soup.find('title')
  try:
    urlTitleText = urlTitle.text
  except:
    try:
      t = lxml.html.parse(url)
      urlTitleText = t.find(".//title").text
    except:
      print "title not found"
      print url
      urlTitleText = ""
  
  return urlTitleText.lower()


def makeURLSet(filename):
  f = open(filename,'r')
  count = 0
  for line in f.read().split('\n'):
    if (re.match("http",line.lower())):
        
      if line.rstrip("/") == line:
          if line != "" and not re.search("html$",line) and not re.search("htm$",line) and not re.search("css$",line):
            line =  line + "/"
            
      title = getTitle(line)
      
      l = Link(line, title)
      
      urlUrlIDPair[line] = count
      
      urlDict[count] = l
      count = count + 1
  f.close()
  print "File scan complete"
  
def genTransProbMat(matrix):
  for row in range(0,len(matrix)):
    sum = 0
    for col in range(0,len(matrix)):
      sum = matrix[row][col] + sum
    for col in range(0,len(matrix)):
      if not sum:
        matrix[row][col] = 1/len(matrix)
      else:
        matrix[row][col] = matrix[row][col]/sum
  return matrix
  
def genPMat(matrix,dFactor):
  matrix1 = numpy.multiply(matrix,1-dFactor)
  uMatrix = numpy.ones((len(matrix),len(matrix)))
  matrix2 = numpy.multiply(uMatrix,dFactor/len(matrix))
  matrix = matrix1 + matrix2
  return matrix
  
def cmpMatrix(mat1,mat2):
  for row in range(0,len(mat1)):
    for col in range(0,len(mat1)):
      if(mat1[row][col] != mat2[row][col]):
        return 1
        
  return 0
  
def genPageRankVector(matrix):
  x = numpy.zeros(shape=(1,len(matrix)))
  rows,cols = x.shape
  for row in range(0,rows):
    for col in range(0,cols):
      x[row][col] = 1/len(matrix)
  
  i = 0
  oldMatrix = x
  newMatrix = numpy.dot(x,matrix)
  
  while cmpMatrix(oldMatrix,newMatrix):
    oldMatrix = newMatrix
    newMatrix = numpy.dot(oldMatrix,matrix)
    i = i+1

  return newMatrix

def printUrlDict():
  for key in urlDict:
    print key, urlDict[key]
    
def writeMetadata(newMatrix):
  print "\nMetadata"
  mString = ""
  for urlID in sorted(urlDict.iterkeys()):
    l = urlDict[urlID]
    l.setPageRank(newMatrix[0][urlID])
    mString = mString + str(urlID) + " " + str(newMatrix[0][urlID])
    anchorSet = set()
    for ele in l.anchorText:
      eleSplit = ele.split(" ")
      for word in eleSplit:
        if word not in stopList:
          anchorSet.add(word)
    
    for term in anchorSet:
      mString = mString + " " + term
  
    mString = mString + "\n"
    
  print mString
  f = open('metadata.txt', 'w')
  f.write(mString)
  f.close()

def saveDict():
  output = open('indexRecord.pkl', 'wb')
  pickle.dump(urlDict, output)
  output.close()
    
def main():
  filename='test.txt'
  print "Please be patient. As we are downloading and reading 328 html files, it will take time to generate MetaData, Pagerank Matrix and Index-Record"
  makeURLSet(filename)
  matrix = traverseURLSet()
  print matrix
  
  matrix = genTransProbMat(matrix)
  #print matrix
  
  dFactor = 0.15
  matrix = genPMat(matrix,dFactor)
  #print matrix
  
  newMatrix = genPageRankVector(matrix)
  #print newMatrix
  
  writeMetadata(newMatrix)
  #printUrlDict()
  saveDict()
  
if __name__ == "__main__":
    main()