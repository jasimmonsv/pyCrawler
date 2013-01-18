#! /usr/bin/python
#Python Version 2.1
#
#This script will crawl a web pages links (specified by the seed global variable) and build a tree list 
#and then proceed to crawl those links within the scope of being on the accepted servers list.
#
import urllib2
import re
import time
from urlparse import urlparse
from urlparse import urljoin
from urlparse import urlsplit
from urlparse import ParseResult
from urlparse import urlunparse
import sys

masterTLD = ['.com','.edu','.org']
masterFileFormat = ['.html','.htm','.php','.asp','.aspx','.jsp','.css','.cfm','.doc','.pdf']
#define which servers to stay within - script will not crawl any pages outside these domains
acceptedServers = ['redkeep.com','jasimmonsv.com']
#vars needed for cookie/session authentication
CFID = '77514'
CFTOKEN = '59455161'
#define your seeded webpage here to begin crawling
try:
    seed=sys.argv[1]
except IndexError:
    seed ='http://google.com'

##########################################################
###################CLASSES################################
##########################################################
class WebPage:
    
    #default constructor to build blank WebPage
    def __init__(self, initSeed):
        self.links = []
        self.seed = initSeed
        self.status = str()
        self.reason = str()
        self.server, self.path = addressBreaker(initSeed)
        self.path = str()

    #crawl_page function allows the WebPage class to crawl itself using multi-node tree logic
    #@input self self referrer
    #@output none
    def crawl_page(self):
        tempArray = []
        print str(self.seed)
        serverCheck = getDomain(self.seed)
        if (self.seed in crawled): #skips pulling url if already called... need to add another round to data to populate missed data.
            self.status = 100
            self.reason='Already Crawled'
            return
        self.seed, content, self.status, self.reason = getURL(self.seed) #entire webpage, status code, status reason
        if serverCheck not in acceptedServers: #check that the page's server is on the acceptedServers list
            crawled.append(self.seed)
            return #drop out of this current iteration
        elif self.status == '200': #otherwise check that page was successfully retrieved.
            union(tempArray, get_all_links(content, self.seed)) #add all links within the page to a temp array
            crawled.append(self.seed) #add current page to crawled array
            for e in tempArray: self.links.append(WebPage(e)) #add all links within temp array to self.links array
            for e in range(len(self.links)): self.links[e].crawl_page() #depth-first crawl through self.links array

    #printLinks function prints the links to the screen
    #@input self self referrer
    #@input n level of child node from parent
    def printLinks(self,n):
        print n*'|'+'-'+self.seed
        for e in self.links:
            e.printLinks(n+1)
    
    #savePages function writes the pages to a file pointer f
    #@input self self referrer
    #@input n level of child node from parent
    #@input f file pointer
    #@output none
    def savePages(self, n, f):
        #f.write(n*'|'+'-'+self.seed+':'+str(self.status)+'\n')
        f.write('<Page pageName="'+self.seed+'" status="'+str(self.status)+'">\n')
        for e in self.links:
            e.savePages(n+1, f)
        f.write('</Page>\n')
        
    def troubleReport(self, f):
        for e in self.links:
            if (str(e.status) != '200'): 
                if (str(e.status) != '100'):
                    f.write('"'+str(e.status)+'","'+self.seed+'","'+e.seed+'"\n')
        for e in self.links:
            if str(e.status) == '200':
                e.troubleReport(f)                
##########################################################
#########END CLASSES######################################
##########################################################

# request the page
#@input page link to a single webpage
#@output data entire webpage code
#@output status code 
#@output status reason
def getURL(page):

    #build http connection
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie','CFID='+CFID+'; CFTOKEN='+CFTOKEN))
    #opener.addheaders.append(('User-agent','Testing Web Crawling Daemon'))
   
    #request connection
    try:
        r1 = opener.open(page)
        #get response
        data = r1.read()
        if str(r1.code) != '200': return page, -1, r1.code, r1.msg
        #close the connection cleanly
    except Exception as inst:
        print "Error connecting to site: "+str(page)
        if type(inst) == urllib2.HTTPError:
            return page, -1, inst.code, inst.msg
        else: return page, -1, 0, inst
    finally:
        opener.close()
    return r1.geturl(), data, str(r1.code), r1.msg
#Calls the get_next_target method to retrieve web links one link at a time, and saves 
#to an array named links.
#@input page
#@links array of links contained within a given page
def get_all_links(page, ServerAdr):
    links=[]
    if page == -1:return links
    while True:
        url, endpos = get_next_target(page)
        if url:
            url = sanatizeURL(url,ServerAdr)#This is key function. Sanatize URLs so nothing slips past
            if url != -1:links.append(url)
            page=page[endpos:]
        else:
            break #url == -1 when there are no more urls to capture from the given page
    return links

#parse the page and return the part within a HREF tag
#@input page a single web page to parse through
#@output url a given url
#@output end_quote the position of the final quote
def get_next_target(page):
    singleCheck = checkPage(page) #remove double printing of errors in next statement
    if singleCheck == None or singleCheck == -1: return None,0
    t = re.findall('href=',page,re.I) #gives results of regular expression search case insensitive
    if len(t)<1: return None,0
    start_link = page.find(t[0])
    if start_link ==-1:
        return None,0
    start_quote=start_link+5
    temp_Quote=page[start_quote] #grabs the type of quote " or '
    end_quote=page.find(temp_Quote,start_quote+1) #looks for the other end of the given quote above
    url=page[start_quote+1:end_quote]
    return url,end_quote

  
#Union function takes array q and adds contents into array p
#@input p final array to work with later
#@input q array that contains items to added into array p
def union(p, q):
    for e in q:
        if e not in p:
            p.append(e)

 
#Checks page for "http:"
#@input page
#@output page
#@error return -1 if error.
def checkPage(page):
    if page==None: return -1
    if not isinstance(page,str):return -1
    if page.find('http:')>=0:
        return page[page.find('http:'):]
    elif page.find('https:')>=0:
        return page[page.find('https:'):]
    #TODO add image checking elif page.find('src='):return page[page.find('src='):]
    else: return -1

  
#takes results of "href=" and transforms into valid link
#@input page url of page to crawl
#@output page sanitized page or url
def sanatizeURL(page, serverAdr):
    assert page != None, "sanatizeURL failed: page type None"
    assert serverAdr != None, "sanatizeURL failed: serverAdr type None"
    assert type(page) == str, str("sanatizeURL failed: page not of type str: {}").format(page) 
    assert type(serverAdr) == str, "sanatizeURL failed"
    assert len(page)!=0 or len(serverAdr)!=0, "sanatizeURL failed"
    page = page.strip()
    o = urlparse(page)
    p = urlparse(serverAdr)
    
    if o.scheme == 'mailto':return -1
    if o.path[:2]=='..':return -1
    if  o.netloc == '':
        if o.path == p.netloc+'/':
            o = urlparse('http://'+o.netloc+o.path+o.params+o.query+o.fragment)
        else: o = urlparse(urljoin(serverAdr,o.path))
    if o.path == '':o = urlparse(o.scheme+'://'+o.path+o.netloc+o.path+'/'+o.params+o.query+o.fragment)  
    return o.geturl()
  
  
#Function breaks apart a link found in a given page
#@input page This is the entire webpage to find contained links.
#@output returns the server path and the remaining page yet to be parsed    
def addressBreaker(page):
    page = checkPage(page)
    if not isinstance(page, str):return -1, -1
    if len(page)>0:
        o = urlparse(page)
        return o.netloc ,o.path
    return -1, -1

def getDomain(page):
    server, path = addressBreaker(page)
    if server == -1 or server == None: return -1
    tld = server[server.rfind('.'):]
    server = server[:server.rfind('.')]
    domain = server[server.rfind('.')+1:]
    return domain+tld
  
########################################################<module>###################################################################
    
start = time.time()
crawled = []
rootPage = WebPage(seed)
rootPage.crawl_page()
import random
with open('./results.'+str(start)+'.xml','w') as f:
    f.write('<Website>\n')
    rootPage.savePages(0,f)
    f.write('</Website>\n')
f.closed  
with open('./openIssues.'+str(start)+'.csv','w') as f:
    rootPage.troubleReport(f)
f.closed
  
#crawled, errors, notCrawled = crawl_web(seed)
#with open('./notCrawledFile', 'w') as f:
#  for e in notCrawled:
#    f.write(e+'\n')
#f.closed'''
print 'Time Elapsed: '+str(time.clock() - start)
