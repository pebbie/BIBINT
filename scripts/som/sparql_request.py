import json
import requests
import sys

def run_sparql(host, query, format="application/json", filename=""):
    params={
        "default-graph": "",
        "should-sponge": "soft",
        "query": query,
        "debug": "on",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": filename
    }
    r = requests.get(host, params=params)
    if r.status_code==requests.codes.ok:
        try:
            return r.json()
        except:
            return {}
    else:
        return {}

if __name__=="__main__":
    if len(sys.argv)>1:
        print json.dumps(run_sparql("http://localhost:8890/sparql/", sys.argv[1]), indent=2)