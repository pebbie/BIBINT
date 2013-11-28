import urllib, json
import sys

# HTTP URL is constructed accordingly with JSON query results format in mind.

def sparqlQuery(query, baseURL, format="application/json"):
    params={
        "default-graph": "",
        "should-sponge": "soft",
        "query": query,
        "debug": "on",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": ""
    }
    querypart=urllib.urlencode(params)
    response = urllib.urlopen(baseURL,querypart).read()
    return response
    #return json.loads(response)

def dump_doc_kw_pair(filename):
    dsn="http://pebbie.net/bibint/1/"
    query = """
        PREFIX ieeedoc: <http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=>
        
        SELECT 
        ?doc, ?keyword
        FROM <%s>
        WHERE {
         ?doc prism:keyword ?keyword.
        }
    """% (dsn)
    data=sparqlQuery(query, "http://localhost:8890/sparql/", format="text/csv")
    with open(filename, "wb") as fo:
            fo.write(data)

def dump_keyword(year):
    # Setting Data Source Name (DSN)
    dsn="http://pebbie.net/bibint/1/"
    
    """
    # number of document
    select 
 COUNT(?doc) as ?doccount 
from <http://pebbie.net/bibint/1/> where { 
?doc a foaf:Document. 
}

# number of publication by year
select 
 ?year, COUNT(?year) as ?yearlycount 
from <http://pebbie.net/bibint/1/> where { 
?doc dcterms:issued ?year. 
} 
GROUP BY ?year
ORDER BY ASC(?year)

#autor rank
select 
      ?autor, COUNT(?autor) as ?pubcount 
from <http://pebbie.net/bibint/1/> 
where { 
      ?doc dc:creator ?autor. 
} 
GROUP BY ?autor
ORDER BY DESC(?pubcount)
    
    #keyword rank
    select 
 ?keyword, COUNT(?keyword) as ?keywordcount 
from <http://pebbie.net/bibint/1/> where { 
?doc prism:keyword ?keyword. 
} 
GROUP BY ?keyword 
ORDER BY DESC(?keywordcount)
    """
    
    # Virtuoso pragmas for instructing SPARQL engine to perform an HTTP GET
    # using the IRI in FROM clause as Data Source URL
    #
    #?doc dcterms:issued ?year.
    #FILTER (year(?year)=%d)
    query="""
        PREFIX ieeedoc: <http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=>
        
        SELECT 
        ?doc, ?keyword
        FROM <%s>
        WHERE {
         ?doc prism:keyword ?keyword.
        }""" % (dsn)
        
    data=sparqlQuery(query, "http://localhost:8890/sparql/", format="text/csv")
    with open("%s.csv" % year, "wb") as fo:
            fo.write(data)

if __name__ == "__main__":
    if len(sys.argv)==2:
        dump_keyword(sys.argv[1])
    if len(sys.argv)>2:
        year_start = int(sys.argv[1])
        year_stop = int(sys.argv[2])
        for y in range(year_start, year_stop+1):
            dump_keyword(y)