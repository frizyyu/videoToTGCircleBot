import json


def read_conf(filename):
    with open(filename) as f:
        return json.load(f)


'''def update_conf(lst):
    global conf
    with open("conf.json", "wb") as f:
        pickle.dump(lst, f)
        f.close()
    conf = lst'''
