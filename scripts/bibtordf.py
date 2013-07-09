#!python
"""
Author              : Peb Ruswono Aryan

requirements    : RDFLib >=3, pybtex
"""
import os
import sys
import glob
import logging
import json
import ConfigParser
from urllib import quote_plus
from optparse import OptionParser

from rdflib import ConjunctiveGraph, Namespace, exceptions
from rdflib import URIRef, RDFS, RDF, OWL, BNode, Literal, XSD
import rdfextras
from rdflib_sqlalchemy.SQLAlchemy import SQLAlchemy
from rdflib_sqlite.SQLite import SQLite

rdfextras.registerplugins()

from pybtex.database.input import bibtex

__version__ = "0.3.0"
"""
version history:
0.4.0   import citation only in directories
           wrap db graph store (sqlalchemy and sqlite)
0.3.0   import single citation only to graph store
0.2.0   add option parser
            multiple mapping of single key
            add datatype (hardcode)
            add logging
            use rdf store backend
0.1.2   implicit option parsing
           use mapping from SPAR (fabio, cito, frbr)
0.1.1   create initial bibtex loader, output to screen
"""

def changefileext(filename, newext):
    if '.' in filename: return ''.join([filename[:filename.rindex('.')], newext])
    return filename
    
def db_graph(url):
    create=True
    if url.lower().startswith('sqlalchemy:'):
        db = ConjunctiveGraph('SQLAlchemy')        
        openstr = url[11:]
        log.info("abs path %s" % openstr)
        db.open(openstr,create=create)
    elif url.lower().startswith('sqlite://'):
        db = ConjunctiveGraph('SQLite')
        openstr = url[url.index('://')+3:]
        create=not os.path.exists(openstr)
        log.info("abs path %s" % openstr)
        db.open(openstr,create=create)
    elif url.lower().startswith('virtuoso'):
        from virtuoso.vstore import Virtuoso
        store = Virtuoso("DSN=VOS;UID=dba;PWD=dba;WideAsUTF16=N")
        db = ConjunctiveGraph(store, 'virtuoso')
    return db
    

#logging facility
log = logging.getLogger('bibtordf')
log.setLevel(logging.DEBUG)
print __file__
fh = logging.FileHandler(changefileext(__file__, '.log'))
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(ch)

default_ext = {"turtle":".ttl", "xml":".rdf"}

def default_config():
    config = {}
    prefix = {}
    prefix["xsd"] = Namespace("http://www.w3.org/2001/XMLSchema#")
    
    prefix["dc"] = Namespace("http://purl.org/dc/elements/1.1/")
    prefix["dcterms"] = Namespace("http://purl.org/dc/terms/")
    prefix["foaf"] = Namespace("http://xmlns.com/foaf/0.1/")
    prefix["swrc"] = Namespace("http://swrc.ontoware.org/ontology#")
    
    prefix["frbr"] = Namespace("http://purl.org/vocab/frbr/core#")
    prefix["fabio"] = Namespace("http://purl.org/spar/fabio/")
    prefix["cito"] = Namespace("http://purl.org/spar/cito/")
    
    prefix["prism"] = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
    
    config["prefixes"] = prefix
        
    mapping = {}
    # default mapping
    mapping[None] = [
                                    (RDF.type, prefix["foaf"]["Document"]), 
                                    (prefix["dc"]["type"], URIRef("http://purl.org/dc/dcmitype/Text"))
                                    ]
                                    
    mapping["title"] = prefix["dc"]["title"]
    
    mapping["conference"] = prefix["fabio"]["ConferencePaper"]
    mapping["inproceedings"] = [
                                                    prefix["fabio"]["ConferencePaper"], 
                                                    prefix["swrc"]["inProceedings"]
                                                    ]
    
    mapping["doi"] = prefix["prism"]["doi"]
    #mapping["pages"] = [prefix["prism"]["pageRange"], prefix["swrc"]["pages"]]
    mapping["pages"] = prefix["swrc"]["pages"]
    
    mapping["year"] = [
                                    prefix["fabio"]["hasPublicationYear"], 
                                    prefix["dcterms"]["issued"]
                                    ]
                                    
    #mapping["abstract"] = prefix["dc"]["description"]
    mapping["keywords"] = prefix["dc"]["subject"]
    
    mapping["citing"] = prefix["cito"]["cites"]
    mapping["citedby"] = prefix["cito"]["isCitedBy"]
    
    config["mapping"] = mapping
    
    return config
    
def escapestr(strdata):
    return quote_plus(json.dumps(strdata)[1:-1])
    
def bind_test(graph, prefix, namespace):
    if graph.store.namespace(prefix) == None: graph.bind(prefix, namespace)
    
def convert_citation(key, graph, citation_data, config):
    """Converts citation information into RDF Triple using config """
    prefix = config["prefixes"]
    XPL = Namespace("http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=")
    
    for cit_id in citation_data["citing"]:
        graph.add(( XPL[key], prefix["cito"]["cites"], XPL[cit_id] ))
    
    for cit_id in citation_data["citedby"]:
        graph.add(( XPL[key], prefix["cito"]["isCitedBy"], XPL[cit_id] ))

def convert_entries(entry, g, config):
    """Convert bibtex entries into RDF stored in Graph g using configuration config"""
    #shorthand for IEEE xplore database URI
    XPL = Namespace("http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=")
    AXPL = Namespace("ieee:")
    author_url = "http://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&searchWithin=p_Authors:.QT.%s.QT."
    prefix = config["prefixes"]
    mapping = config["mapping"]
    
    # bind it
    
    #bind_test(g, None, XPL)
    bind_test(g, "ieee", AXPL)
    for pref in prefix:
        bind_test(g, pref, prefix[pref])
        
    for key, entry in entry.entries.items():
        log.info( key+ " is "+ entry.type )
        entry_IRI = XPL[key]
        
        if None in mapping:
            item = mapping[None]
            
            if isinstance(item, list):
                for default_entry in item:
                    g.add((entry_IRI, default_entry[0], default_entry[1]))
        
        #generate each person as foaf resource
        if 'author' in entry.persons:
            for person in entry.persons['author']:
                log.debug(escapestr(person.last()))
                person_IRI = URIRef("ieee:%s_%s%s" % (escapestr("".join(person.last())), "".join(person.first()), "".join(person.middle()) ))
                
                g.add(( person_IRI, RDF.type, prefix["foaf"]["Agent"] ))
                
                person_fullname = escapestr("%s,%s%s" % ("".join(person.last()), "".join(person.first()), "".join(person.middle()) ))
                person_seeAlso = URIRef(author_url % (quote_plus(person_fullname)))
                g.add(( person_IRI, RDFS.seeAlso, person_seeAlso ))
                
                g.add(( person_IRI, prefix["foaf"]["lastName"], Literal("".join(person.last()), datatype=XSD.string) ))
                g.add((person_IRI, prefix["foaf"]["firstName"], Literal("".join(person.first()+person.middle()), datatype=XSD.string) ))
                g.add((entry_IRI, prefix["dc"]["creator"], person_IRI))
        
        if entry.type in mapping:
            if isinstance(mapping[entry.type], list):
                for etype in mapping[entry.type]:
                    if isinstance(etype, tuple):
                        g.add(( entry_IRI, etype[0], etype[1] ))
                    else:
                        g.add(( entry_IRI, RDF.type, etype ))
            else:
                g.add(( entry_IRI, RDF.type, mapping[entry.type] ))
                
            if entry.type in ["conference", "inproceedings"] and "booktitle" in entry.fields:
                g.add(( entry_IRI, prefix["frbr"]["partOf"], Literal(entry.fields["booktitle"], datatype=XSD.string) ))
            
        for field, field_value in entry.fields.items():
            if field in mapping:
                if isinstance(mapping[field], list):
                    lit_dtype = XSD.string
                    if field == "year": lit_dtype = XSD.gYear
                    
                    for fieldmap in mapping[field]:
                        g.add(( entry_IRI, fieldmap, Literal(entry.fields[field], datatype=lit_dtype) ))
                else:    
                    g.add(( entry_IRI, mapping[field], Literal(entry.fields[field], datatype=XSD.string) ))
                    
            if field == "keywords":
                keyword_list = entry.fields[field].split(";")
                for keyword in keyword_list:
                    g.add((  entry_IRI, prefix["prism"]["keyword"], Literal(keyword, datatype=XSD.string) ))
                
    g.commit()
        
if __name__ == "__main__":
    log.debug(" ".join(sys.argv))
    
    usage = "Usage: %prog [options]"
    oparser = OptionParser(usage=usage, version=__version__)
    
    # option for single file conversion
    oparser.add_option("-i", "--input", type="string", help="input bibtex file", dest="bib_file")
    oparser.add_option("-o", "--output", type="string", help="output rdf file", dest="rdf_file")
    oparser.add_option("-f", "--format", type="string", help="output format (xml, turtle)", dest="rdf_format", default="turtle")
    
    oparser.add_option("-x", "--citation", type="string", help="input citation file", dest="bib_cit")
    
    # option to get input bibtex files from directory tree
    oparser.add_option("-d", "--dir", type="string", help="input directory path containing bibtex files", dest="bib_dir")
    oparser.add_option("-r", "--recursive", action="store_true", help="do recursive directory walk", dest="recursive", default=False)
    
    oparser.add_option("-n", "--no-bib", action="store_true", help="do citation only", dest="do_cit_only", default=False)
    
    # configuration for mapping bibtex field into appropriate RDF statement
    oparser.add_option("-c", "--config", type="string", help="input filename for mapping configuration", dest="mapping_config")
    
    # configuration for using external triplestore instead of per-file
    oparser.add_option("-t", "--store", type="string", help="put conversion result in the specified store instead of creating separate file", dest="triplestore")
    oparser.add_option("-s", "--store-config", type="string", help="input triplestore configuration", dest="triplestore_config")
    
    option, args = oparser.parse_args()

    #log.info(repr(option))
    
    
    config = default_config()
    output_format = option.rdf_format
    
    if option.mapping_config is not None:
        log.info( option.mapping_config )
    
    if option.bib_file is not None:
        parser = bibtex.Parser()
        log.info("Opening "+option.bib_file)
        bib_data = parser.parse_file(option.bib_file)
        
        if option.triplestore is not None:
            if option.triplestore_config is None:
                log.error("Triplestore configuration must be specified when triplestore name is given")
                exit(1)
                
            g = db_graph(option.triplestore_config)
        else:
            g = ConjunctiveGraph()
        convert_entries(bib_data, g, config)
        
        cit_file = changefileext(option.bib_file, "_citation.json")
        bib_id = changefileext(option.bib_file, "")
        bib_id = os.path.splitext(os.path.basename(bib_id))[0]
        if os.path.exists(cit_file):
            convert_citation(bib_id, g, json.load(file(cit_file)), config)
    
        log.info("saving.. ")
        if option.rdf_file is not None:
            g.serialize(option.rdf_file, format=output_format)
        elif option.triplestore is not None:
            pass
        else:
            log.info( "output filename or triplestore config not given, printing to screen" )
            print g.serialize(format=output_format)
    elif option.bib_dir:
        opt_separate = True
        if option.triplestore is not None:
            if option.triplestore_config is None:
                log.error("Triplestore configuration must be specified when triplestore name is given")
                exit(1)
                
            g = db_graph(option.triplestore_config)
            opt_separate = False
            
        if not option.recursive:
            #use glob            
            files = [f for f in glob.glob(os.path.join(option.bib_dir, "*.bib")) if f.lower().endswith(".bib")]
            for bib_file in files:
                log.info("Opening "+bib_file)
                
                
                if opt_separate: g = ConjunctiveGraph()
                if not option.do_cit_only:
                    parser = bibtex.Parser()
                    bib_data = parser.parse_file(bib_file)
                    convert_entries(bib_data, g, config)
                
                cit_file = changefileext(bib_file, "_citation.json")
                bib_id = changefileext(bib_file, "")
                bib_id = bib_id[bib_id.rindex(os.sep)+1:]
                if os.path.exists(cit_file):
                    convert_citation(bib_id, g, json.load(file(cit_file)), config)
                
                log.info("saving.. ")
                if opt_separate: g.serialize(changefileext(bib_file, default_ext[output_format]), format=output_format)
        else:
            #use os.walk
            for path, dirs, files in os.walk(option.bib_dir):
                bibfiles = [f for f in files if f.lower().endswith(".bib")]
                for f in bibfiles:
                    bib_file = os.path.join(path, f)
                    log.info("Opening "+bib_file)
                    
                    if opt_separate: g = ConjunctiveGraph()
                    if not option.do_cit_only:
                        parser = bibtex.Parser()
                        bib_data = parser.parse_file(bib_file)
                        convert_entries(bib_data, g, config)
                    
                    cit_file = changefileext(bib_file, "_citation.json")
                    bib_id = changefileext(bib_file, "")
                    bib_id = bib_id[bib_id.rindex(os.sep)+1:]
                    if os.path.exists(cit_file):
                        convert_citation(bib_id, g, json.load(file(cit_file)), config)
                    
                    log.info("saving.. ")
                    if opt_separate: g.serialize(changefileext(bib_file, default_ext[output_format]), format=output_format)
                    
        if not opt_separate: g.store.close()
    elif option.bib_cit is not None:
        if option.triplestore is not None:
            if option.triplestore_config is None:
                log.error("Triplestore configuration must be specified when triplestore name is given")
                exit(1)
                
            g = db_graph(option.triplestore_config)
        else:
            g = ConjunctiveGraph()
            
        cit_file = option.bib_cit
        bib_id = cit_file
        if "_citation.json" in bib_id:
            bib_id = bib_id[:bib_id.index("_citation.json")]
        if os.sep in bib_id:
            bib_id = bib_id[bib_id.rindex(os.sep)+1:]
        if os.path.exists(cit_file):
            convert_citation(bib_id, g, json.load(file(cit_file)), config)
            
        if option.triplestore is not None:
            g.store.close()
        else:
            log.info("saving.. ")
            if option.rdf_file is not None:
                g.serialize(option.rdf_file, format=output_format)
            else:
                log.info( "output filename not given, printing to screen" )
                print g.serialize(format=output_format)
    else:
        oparser.print_help()