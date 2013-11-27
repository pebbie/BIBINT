"""filename : dblp.py
    description : script for extracting information from dblp website
"""
import os
import requests
import json
from urlparse import urlparse

def prepare_query(querystr, num_fetch, offset):
    terms = [term.strip()+"*" for term in querystr.split(" ")]
    qterms = " ".join(terms)
    autocomplete_word = 0
    req = "http://dblp.org/search/api/?q=%s&h=%d&c=%d&f=%d&format=json" % (qterms, num_fetch, autocomplete_word, offset)
    print req
    return req
    
def search(querystr, max_fetch=20, item_per_page=10):
    cnt = 2
    offset = 0
    num_fetch = 0
    
    r = requests.get(prepare_query(querystr, 0, offset))
    meta = r.json()
    total = meta['result']['hits']['@total']
    if max_fetch == -1:
        max_fetch = total
    print "total result : ", total
    all_result = []
    while num_fetch < max_fetch:
        r = requests.get(prepare_query(querystr, item_per_page, offset))
        result = r.json()
        docs = result['result']['hits']['hit']
        num_fetch += len(docs)
        all_result += docs
        offset = offset + item_per_page
    return all_result
    
#####################
# extract search results            #
#####################

def doc_type(doc):
    return doc['info']['type']
    
def doc_authors(doc):
    return doc['info']['authors']['author'] if 'authors' in doc['info'] else []
    
def doc_url(doc):
    return doc['info']['title']['@ee'] if '@ee' in doc['info']['title'] else None
    
def extract_types(doclist):
    types = {}
    for d in doclist:
        dtype = doc_type(d)
        if dtype in types:
            types[dtype] += 1
        else:
            types[dtype] = 1
    print json.dumps(types, indent=2)
    return types
    
def extract_authors(doclist):
    authors = []
    for d in doclist:
        authorlist = doc_authors(d)
        if len(authorlist)==0:
            print doc_type(d)
            print json.dumps(d, indent=2)
        else:
            for au in authorlist:
                if au not in authors:
                    authors.append(au)
    return authors
    
def extract_urls(doclist):
    urls = []
    for d in doclist:
        ee = doc_url(d)
        if ee is not None and len(ee)>0:
            urls.append(ee)
    return urls
    
def extract_venues(doclist):
    venues = {}
    for d in doclist:
        v = d['info']['venue']
        if "@journal" in v:
            venues[v["@journal"]] = 1
        elif "@conference" in v:
            venues[v["@conference"]] = 1
        elif "@school" in v:
            venues[v["@school"]] = 1
        elif "@publisher" in v:
            venues[v["@publisher"]] = 1
        else:
            print json.dumps(v, indent=2)
    return venues
    
def extract_docs(doclist):
    docs = {}
    for d in doclist:
        docid = d['@id']
        docs[docid] = d
    return docs
    
def extract_years(doclist):
    years = {}
    for d in doclist:
        year = d['info']['year']
        if year in years:
            years[year] += 1
        else:
            years[year] = 1
    return years
    
#####################
# server identification               #
#####################

def is_springer(req):
    """determines whether the server is springer based on headers
        @param req : requests object
    """
    return 'link' in req.headers and 'link.springer.com' in req.headers['link']
    
def is_ieee(req):
    """determines whether the server is ieee (ieee, computer) based on headers
        @param req : requests object
    """
    return 'set-cookie' in req.headers and ('.ieee.org' in req.headers['set-cookie'] or 'computer.org' in req.headers['set-cookie'])
    
def is_arxiv(req):
    """determines whether the server is arxiv based on headers
        @param req : requests object
    """
    return 'set-cookie' in req.headers and ('.arxiv.org' in req.headers['set-cookie'])
    
def is_sciencedirect(req):  
    """determines whether the server is sd based on headers
        @param req : requests object
    """
    return 'set-cookie' in req.headers and ('.sciencedirect.com' in req.headers['set-cookie'])
    
def is_worldsci(req):
    """determines whether the server is worldscientific based on headers
        @param req : requests object
    """
    return 'set-cookie' in req.headers and ('.www.worldscientific.com' in req.headers['set-cookie'])
    
def is_acm_url(url):
    """determines whether the server is acm based on url pattern
        @param url : parsed url
    """
    return 'acm.org' in url.netloc
    
def is_doi_url(url):
    """determines whether the server is doi proxy
        @param url : parsed url
    """
    return 'dx.doi.org' == url.netloc
    
def is_ieee_url(url):
    """determines whether the server is ieee from url
        @param url : parsed url
    """
    return 'ieeecomputersociety.org' in url.netloc
    
def is_springer_url(url):
    """determines whether the server is springer from url
        @param url : parsed url
    """
    return 'www.springerlink.com' in url.netloc
    
def is_aaai_url(url):
    """determines whether the server from url
        @param url : parsed url
    """
    return 'aaai.org' in url.netloc
    
def is_html(req):
    """check if the resource is html
    """
    return 'content-type' in req.headers and ('text/html' in req.headers['content-type'])
    
def determine_server(urls):
    """skeleton for determining handling
    """
    for url in urls:
        print url, 
        purl = urlparse(url)
        
        if is_acm_url(purl):
            print "is acm"
        elif is_ieee_url(purl):
            print "is ieee"
        elif is_springer_url(purl):
            print "is springer"
        elif is_aaai_url(purl):
            print "is aaai"
        else:
        #elif is_doi_url(purl):
            r =  requests.get(url)
            print r.status_code,
        
            if is_springer(r):
                print "is springer"
            elif is_ieee(r):
                print "is ieee"
            elif is_worldsci(r):
                print "is worldscientific"
            elif is_arxiv(r):
                print "is arxiv"
            elif is_sciencedirect(r):
                print "is arxiv"
            else:
                print json.dumps(r.headers, indent=2)
                # get extra info from curl
                if is_html(r):
                    print os.system("curl %s" % url)
            
    
#####################
# main                                       #
#####################

if __name__ == "__main__":
    result = search("semantic web", 50)
    years = extract_years(result)
    print sorted(years.items(), key=lambda x: x[1], reverse=True)
   
    extract_authors(result)
    extract_venues(result)
    urls = extract_urls(result)
    extract_types(result)
   
    print len(result)
   
    determine_server(urls[30:40])
    