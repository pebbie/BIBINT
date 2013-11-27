import os
import sys

def filter_quote(s):
    ieee_ns = "http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber="
    if ieee_ns in s:
        s = s.replace(ieee_ns, "ieeedoc:")
    if s.startswith('"'):
        return s[1:]
    elif s.endswith('"'):
        return s[:-1]
    else: 
        return s
    
def parse_line(s):
    line = s.split('","')
    line = [filter_quote(col) for col in line]
    return line

if __name__=="__main__":
    if len(sys.argv)>1:
        year = int(sys.argv[1])
        
        year_csv = "%d.csv" % year
        with open(year_csv) as f:
            lines = f.readlines()
            lines = [parse_line(line.strip()) for line in lines]
            
        doc = []
        kw = []
        kwd = {}
        for row in lines[1:]:
            if not row[0] in doc: doc.append(row[0])
            if not row[1] in kw: 
                kw.append(row[1])
                kwd[row[1]] = [len(doc)-1]
            kwd[row[1]].append(doc.index(row[0]))
        
        print len(doc), len(kw)        
    
        if not os.path.exists(sys.argv[1]):
            os.mkdir(sys.argv[1])
        
        data_vec = os.path.join(sys.argv[1], "%d.vec" % year)
        print data_vec
        with open(data_vec, "wb") as f:
            f.write("$TYPE vec_kwdoc\n")
            f.write("$XDIM %d\n" % len(kw))
            f.write("$YDIM 1\n")
            f.write("$VEC_DIM %d\n" % len(doc))
            for keyword in kw:
                base = [0]*len(doc)
                for doc_id in kwd[keyword]:
                    base[doc_id] = 1
                f.write("%s %s\n" % (" ".join([str(b) for b in base]), keyword.replace(" ", "_")))
            
        template_vec = os.path.join(sys.argv[1], "%d.tv" % year)
        with open(template_vec, "wb") as f:
            f.write("$TYPE template\n")
            f.write("$XDIM %d\n" % 2)
            f.write("$YDIM %d\n" % len(kw))
            f.write("$VEC_DIM %d\n" % len(doc))
            for f_nr, attr in enumerate(doc):
                f.write("%d %s\n" % (f_nr, attr))
        
        print lines[:10]
            