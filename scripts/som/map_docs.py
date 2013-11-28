from read_output import parse_som_unit
from csv2som import filter_quote
import requests
import rdflib

from sparql_request import run_sparql

endpoint = "http://localhost:8890/sparql/"
unit = None
docs = None
dloc = None
keyloc = None

def parse_doc_kw(filename):
    """
    load csv and returns a map from document to list of keyword of that document
    """
    result = {}
    isFirst = True
    with open(filename, "rb") as f:
        for line in f.readlines():
            if isFirst:
                isFirst = False
                continue
            tmp = line.strip()
            if len(tmp)==0: continue
            part = [filter_quote(col) for col in tmp.split('","')]
            doc, keyword = tuple(part)
            if part[0] in result:
                result[doc].append(keyword)
            else:
                result[doc] = [keyword]
    return result
    
def set_doc_coord():
    global docs
    docloc = {}
    for doc in docs:
        docloc[doc] = get_coord(docs[doc])
    return docloc
    
def get_coord(kwlist):
    global keyloc
    lx = []
    ly = []
    for kw in kwlist:
        if kw in keyloc:
            x, y = keyloc[kw]
            lx.append(x)
            ly.append(y)
    #print len(lx), len(ly), kwlist
    xa, ya = -1, -1
    if len(lx)>0 and len(ly)>0:
        xa = sum(lx)*1.0/len(lx)
        ya = sum(ly)*1.0/len(ly)
    return (xa, ya)
    
def inv_keyword_pos(map):
    """
    Compute inverse map from grid of keyword to map from keyword to location in the grid
    """
    result = {}
    for row in xrange(map["YDIM"]):
        for col in xrange(map["XDIM"]):
            for keyword in map["DATA"][row][col]:
                result[keyword] = (col, row)
    return result

#
#   Web interface
#
    
from bottle import *

@route("/")
@view("index")
def index():
    global unit
    return {}
    
@route("/unit/<y:int>/<x:int>")
def get_cell(y,x):
    global unit
    return dict(keyword=unit["DATA"][y][x])
    
@route("/unit.json")
def dump_unit():
    global unit
    return unit["DATA"]
    
@route("/unitdata.json")
def unit_d3():
    global unit
    result = []
    for row in xrange(unit["YDIM"]):
        for col in xrange(unit["XDIM"]):
            num_key = len(unit['DATA'][row][col])
            if num_key>0:
                result.append(dict(x=col,y=row,num=num_key))
    return dict(result=result)
    
@route("/docs.json")
def dump_docs():
    global docs
    return docs
    
@route("/locs.json")
def dump_dloc():
    global dloc
    return dloc
    
@route("/years.json")
def get_years():
    global endpoint
    query = """
    SELECT
     ?year, COUNT(?year) as ?yearlycount 
    from <http://pebbie.net/bibint/1/> where { 
    ?doc dcterms:issued ?year. 
    } 
    GROUP BY ?year
    ORDER BY DESC(?year)
    """
    return run_sparql(endpoint, query)
    
@route("/authors.json")
def get_authors():
    global endpoint
    query = """select 
      ?autor, COUNT(?autor) as ?pubcount 
        from <http://pebbie.net/bibint/1/> 
        where { 
              ?doc dc:creator ?autor. 
        } 
        GROUP BY ?autor
        ORDER BY DESC(?pubcount) 
        LIMIT 100"""
    return run_sparql(endpoint, query)

if __name__ == "__main__":
    unit = parse_som_unit("0\\AUTH_KW.unit.gz")
    keyloc = inv_keyword_pos(unit)
    docs = parse_doc_kw("0.csv")
    dloc = set_doc_coord()
    print len(docs), "documents"
    debug(True)
    run(port="2013", server="paste", reloader=True)