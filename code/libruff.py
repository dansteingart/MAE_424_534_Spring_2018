##Author: Dan Steingart
##Date Started: 2017-09-01
##Notes: Pull Specta from libRuff

from pithy import *
import requests as r
from pprint import pprint as pp 
from commands import getoutput as go
import glob

ub = "http://rruff.info/repository/sample_child_record_powder/by_minerals/"


def parseCP(params):
    ps = params.split("\r\n")
    header = ps[0]
    theta = []
    count = []
    for p in ps[1:]:
        d = p.split(",")
        if len(d) > 1:
            theta.append(float(d[0]))
            count.append(float(d[1]))
    out = {}
    out['header'] = header
    out['theta'] = array(theta)
    out['counts'] = array(count)
    return out

def get(mineral,debug=False):
    go("mkdir -p files/rruff/")    
    cache = glob.glob("files/rruff/*")
    cached = False

    try:        
        data = open("files/rruff/"+mineral+".txt").read()
        data = data.split("##")
        if debug:print "pulling cache"

    except:    
        print "no cache"
        uf = ub+mineral+".txt"
        a = r.get(uf)
        open("files/rruff/"+mineral+".txt",'w').write(a.text)
        data = a.text.split("##")
    out = []
    for d in data: out.append(d.split("="))
    data = out
    out = {}
    for d in data:
        if len(d)>1:
            out[d[0]] = d[1]
    out['CELL PARAMETERS'] = parseCP(out['CELL PARAMETERS'])
    return out
    


if __name__ == "__main__":
    data = get("Diamond__R050204__Powder__Xray_Data_XY_RAW__6459")
    plot(data['CELL PARAMETERS']['theta'],data['CELL PARAMETERS']['counts'])
    showme()
    clf()