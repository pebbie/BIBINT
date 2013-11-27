import gzip
import os


def parse_som_unit(filename):
    f = gzip.open(filename, "rb")
    last_key = ""
    info = {}
    is_var = False
    #print os.path.splitext(filename)
    store_value = False
    
    for line in f.readlines():
        if line.startswith("#"): 
            continue
        is_var = line.startswith("$")
        if is_var:
            sep = None
            if " " in line:
                sep = line.index(" ")
                var_value = line[sep+1:].strip()
                
            var_name = line[1:sep].strip()
        else:
            var_value = line.strip()
            
        #parsing logic
        if is_var:
            if var_name in ["XDIM", "YDIM"]:
                info[var_name] = int(var_value)
                if "XDIM" in info and "YDIM" in info:
                    info["DATA"] = []
                    for row in xrange(info["YDIM"]):
                        tmp = []
                        for col in xrange(info["XDIM"]):
                            tmp.append([])
                        info["DATA"].append(tmp)
            elif var_name in ["POS_X", "POS_Y"]:
                if store_value: 
                    store_value = False
                info[var_name] = int(var_value)
            elif var_name == "MAPPED_VECS":
                cur_x = info["POS_X"]
                cur_y = info["POS_Y"]
                del info["POS_X"]
                del info["POS_Y"]
                store_value = True
            else:
                pass
        else:
            if store_value:
                #if info["DATA"][cur_y][cur_x] is None: info["DATA"][cur_y][cur_x] = []
                info["DATA"][cur_y][cur_x].append(var_value)
    f.close()
    return info

if __name__ == "__main__":    
    unit = parse_som_unit("0\\AUTH_KW.unit.gz")
    #print len(unit["DATA"]), unit["DATA"][0][0]
    cnt = []
    for y in xrange(unit["YDIM"]):
        for x in xrange(unit["YDIM"]):
            cnt.append(len(unit["DATA"][y][x]))
            
    scnt = sorted(cnt, reverse=True)
    total = sum(scnt)
    avg = total / (unit["XDIM"]*unit["YDIM"])
    print scnt[0], scnt[-1], avg