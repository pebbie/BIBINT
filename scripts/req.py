import requests
import json
from urlparse import urlparse
import sys

if __name__ == "__main__":
    if len(sys.argv)>1:
        print urlparse(sys.argv[1])
        r =  requests.get(sys.argv[1])
        print r.status_code,
        print json.dumps(r.headers, indent=2)