import os
import sys
import glob

import mechanize
from mechanize._beautifulsoup import BeautifulSoup, Tag
import json
import math
from urlparse import urlparse
from collections import deque
from time import sleep
from random import randint
import httplib

base_url = u"http://ieeexplore.ieee.org"
conn = None

def fetch(url):
    
    global conn, base_url
    if conn is None: 
        print base_url[base_url.index("//")+2:]
        conn = httplib.HTTPConnection(base_url[base_url.index("//")+2:])
    conn.request('GET', url[len(base_url):])
    fp = conn.getresponse()
    
    #fp = mechanize.urlopen(url)
    source = fp.read()
    #fp.close()
    return source
    
def save(url,local_path):
    source = fetch(url)
    slen = len(source)
    if os.path.exists(local_path):
        dlen = os.path.getsize(local_path)
        if slen == dlen:
            return False
    with open(local_path, 'wb') as fo:
        fo.write(source)
    return True
    
def from_file(local_path):
    result = None
    with open(local_path, "rb") as f: result = f.read()
    return result
    
def to_file(local_path, data):
    with open(local_path, "wb") as f: f.write(data)
    
def extract_pagecount(soup, pagenumber = 25):
    count = soup.find("span", {"class": "display-status results-returned"}).string.strip()
    count = int(count.split(' ')[0])
    pagecount = count / pagenumber
    if count % pagenumber > 0: pagecount += 1
    return count, pagecount
    
def extract_searchresult(soup, itemslist):
    for li in soup.find("ul", {"class" : "Results"}).contents:
        if isinstance(li, basestring): continue

        det = li.find('div', {'class': 'detail'})
        item = {'authors':[]}
        itemslist.append(item)
        
        for child in det.contents:
            if isinstance(child, Tag):
                if child.name == 'h3':
                    #parse title
                    if child.a is not None:
                        
                        title_parts = []
                        for part in child.a.contents:
                            if isinstance(part, basestring):
                                title_parts.append(part.strip())
                            elif isinstance(part, Tag):
                                if part.name != "br":
                                    title_parts += [part.string]
                        title = " ".join(title_parts)
                        item['title'] = title
                    
                        arurl  = base_url + child.a['href']
                        urlp = urlparse(arurl)
                        q = dict(par.split("=") for par in urlp.query.split("&") if "=" in par)
                        item['articleId'] = q['arnumber']
                    
                elif child.name == 'a':
                    #parse authors
                    prefName = child.find('span', {'id': 'preferredName'})
                    if prefName is not None:
                        author = {'preferredName': prefName['class']}
                        authorId = child.find('span', {'id': 'authorId'})
                        if authorId is not None:
                            author['authorId'] = authorId['class']
                            
                        item['authors'].append(author)

            elif isinstance(child, basestring):
                if "Publication Year" in child:
                    item['year'] = int(child.strip().split(":")[1].strip())
    
def parse_search(doc, result=None, item_per_page = 25):
    s = BeautifulSoup(doc)
    
    if result is None:
        count, pagecount = extract_pagecount(s, item_per_page)
        print count, pagecount

        result = {'count': count, 'pages': pagecount}
        result['items'] = []
        
    extract_searchresult(s, result['items'])
    print len(result['items'])
    return result
    
def view_article(id):
    detail = base_url + "/xpl/articleDetails.jsp?tp=&arnumber="+id
    references = base_url + "/xpl/references.jsp?arnumber="+id
    citationmap = base_url + "/xpl/mwCitations.jsp?tp=&arnumber="+id
#    citation = base_url + "/xpl/downloadCitations?fromPage=&citations-format=citation-only&download-format=download-bibtex&recordIds="+id

def get_article_references(articleId):
    ref_url = base_url + "/xpl/references.jsp?reload=true&arnumber="+articleId
    return ref_url

def get_citation_map(articleId):
    cm_url = base_url + "/xpl/mwCitations.jsp?reload=true&tp=&arnumber="+articleId
    return fetch(cm_url)
    
def urltoarnumber(u):
    return [term.split("=")[1] for term in urlparse(u).query.split("&") if "arnumber" in term][0]
    
def parse_citmap(doc):
    def get_docs(sp):
        out = []
        if sp is not None:
            for a in sp.findAll("a"):
                try:
                    if "articleDetails" in a["href"]:
                        up = urltoarnumber(a['href'])
                        if up not in out: out.append(up)
                except:
                    pass
        return out
    #to_file("dump.soup", doc)
    soup = BeautifulSoup(doc)
    citing = get_docs(soup.find("div", {'id':'colFirst'}))
    citedby = get_docs(soup.find("div", {'id':'colSecond'}))
        
    return dict(citing=citing, citedby=citedby)
    
def get_article_citation(articleId, withAbstract=False, format=u'bibtex'):
    #citations-format = citation-only | citation-abstract
    cit_dl = u"only"
    if withAbstract: cit_dl = u"abstract"
    #download-format = download-ascii | download-bibtex | download-refworks | download-ris
    citation_url = base_url + u"/xpl/downloadCitations?reload=true&fromPage=&citations-format=citation-"+cit_dl+u"&download-format=download-"+format+u"&recordIds="+articleId
    return fetch(citation_url).replace("<br>", "")

def search_doc(query_str, item_per_page=25, page=1):
    search_url = base_url + "/search/searchresult.jsp?newsearch=true&queryText=" + query_str.replace(" ", "+")+ "&rowsPerPage=" + str(item_per_page) + "&pageNumber=" + str(page)
    return search_url
    
def search_by_author(authorName,authorId=None, item_per_page=25):
    url = base_url + "/search/searchresult.jsp?newsearch=true&searchWithin=p_Authors:."+authorName.replace(" ", "%20")+"."
    if authorId is not None:
        url += "&searchWithin=p_Author_Ids:"
    return url
    
def parse_search_result(query_str, item_per_page=25):
    print "fetching ",
    doc = fetch(search_doc(query_str, item_per_page=item_per_page))
    print "parsing..."
    result = parse_search(doc, item_per_page=item_per_page)
    numpages = result['pages']
    for i in xrange(2, numpages+1):
        doc = fetch(search_doc(query_str, item_per_page=item_per_page,page=i))
        print "parsing..."
        result = parse_search(doc, item_per_page=item_per_page, result=result)
    print result['count'], len(result['items'])
    return result
    
def acm(query_str):
    acm_url = u"http://dl.acm.org/"
    cookieJar = mechanize.CookieJar()

    opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
    mechanize.install_opener(opener)
    
    fp = mechanize.urlopen(acm_url)
    forms = mechanize.ParseResponse(fp, backwards_compat=False)
    fp.close()
    #doc = fetch(acm_url)
    form = forms[0]
    form['query'] = query_str
    fp = mechanize.urlopen(form.click())
    doc = fp.read()
    with open("acm.html", 'wb') as fo:
        fo.write(doc)
    fp.close()
    
def download_one(articleId, target_dir=''):
    item = articleId
    print "downloading ", item
    local_item = os.path.join(target_dir, "%s.bib" % item)
    item_link = os.path.join(target_dir, "%s_citation.json" % item)
    if not os.path.exists(local_item):
        to_file(local_item, get_article_citation(item, True))
    if not os.path.exists(item_link):
        citation = parse_citmap(get_citation_map(item))
        with open(item_link, "wb") as f: json.dump(citation, f, indent=4, sort_keys=True)
    return citation
    
def crawl(seed_articleId=None):
    min_time = 5
    max_time = 10
    delay_enabled = False
    buffer_file = "buffer.txt"
    item = None
    print "crawling for ", seed_articleId
    try:
        if os.path.exists(buffer_file):
            with open(buffer_file, "r") as b: agenda = deque([l.strip() for l in b.readlines()])
        else:
            agenda = deque(seed_articleId)
            
        if seed_articleId is not None and (isinstance(seed_articleId, basestring) or isinstance(seed_articleId, list)):
            agenda = deque(seed_articleId)
        dump_counter = 0
        dump_threshold = 10
        while len(agenda)>0:
            item = agenda.popleft()
            print "downloading ", item
            local_item = os.path.join("data", "%s.bib" % item)
            item_link = os.path.join("data", "%s_citation.json" % item)
            if not os.path.exists(local_item):
                to_file(local_item, get_article_citation(item, True))
            if not os.path.exists(item_link):
                citation = parse_citmap(get_citation_map(item))
                with open(item_link, "wb") as f: json.dump(citation, f, indent=4, sort_keys=True)
                for id in citation['citing']+citation['citedby' ]:
                    if id not in agenda and not (os.path.exists(os.path.join("data", "%s.bib" % id)) and os.path.exists(os.path.join("data", "%s_citation.json" % id))):
                        agenda.append(id)
            print len(agenda)
            dump_counter += 1
            if dump_counter > dump_threshold:
                dump_counter = 0
                with open(buffer_file, "w") as b: b.write("\n".join(agenda))
            if delay_enabled:
                sleep(randint(min_time, max_time))
    except KeyboardInterrupt, SystemExit:
        if not (os.path.exists(local_item) and os.path.exists(item_link)): agenda.appendleft(item)
        with open(buffer_file, "w") as b: b.write("\n".join(agenda))
        print "stopped at %s" % item
        raise
        
def fix(datadir):   
    buffer_file = "buffer.txt"
    if os.path.exists(buffer_file):
        with open(buffer_file, "r") as b: agenda = deque([l.strip() for l in b.readlines()])
    else:
        agenda = deque(seed_articleId)
    files = glob.glob(os.path.join(datadir, "*.bib"))
    for filename in files:
        id = filename[:-4]
        cit_file = "%s_citation.json" % id
        if not os.path.exists(cit_file):
            print id
            id = id[len(datadir)+1:]
            if id not in agenda: agenda.appendleft(id)
        else:
            try:
                with open(cit_file, "rb") as fc: 
                    citation = json.load(fc)
                for cid in citation['citing']+citation['citedby' ]:
                    if cid not in agenda and not (os.path.exists(os.path.join(datadir, "%s.bib" % cid)) and os.path.exists(os.path.join(datadir, "%s_citation.json" % cid))):
                        print cid
                        agenda.append(cid)
            except:
                print cit_file
                with open(buffer_file, "w") as b: b.write("\n".join(agenda))
                raise
            
    with open(buffer_file, "w") as b: b.write("\n".join(agenda))
            #download_one(id)
    
if __name__ == "__main__":
    #result = query_search(search_doc("mobile shooting range", item_per_page=25))
    #result = parse_search_result(search_by_author("P.R. Aryan", item_per_page=25))
    #save(get_citation_map("816044"), "816044.cm")
    #save(get_article_references("6104191"), "6104191_ref.html")
    #save(get_citation_map("6104191"), "6104191_cit.html")
    #parse_citmap(from_file("6104191_cit.html"))
    #acm("risk or analysis")
    #print json.dumps(parse_citmap(from_file("816044.html")), indent=4, sort_keys=True)
    #result = parse_search_result("counter terrorism", 100)
    #with open("output_author.json", "wb") as f : json.dump(result, f, indent=4, sort_keys=True)
    
    #result = json.load(open("output_author.json"))
    #crawl([article['articleId'] for article in result['items'] if 'articleId' in article])
    #crawl()
    if len(sys.argv)>2: #articleId target_dir
        download_one(sys.argv[1], sys.argv[2])
    elif len(sys.argv)>1 and sys.argv[1]=="--fix":
        fix("data")
    else:
        crawl()
    
    
    #print json.dumps(parse_citmap(fetch(get_citation_map("1559623"))), indent=4, sort_keys=True)
    
#    result = parse_search(from_file('author.html'))
#    for article in result['items']:
#        with open(article['articleId']+".bib", "wb") as f : f.write(get_article_citation(article['articleId']))
    
    #with open("output_author.json", "wb") as f : json.dump(result, f, indent=4, sort_keys=<true></true>