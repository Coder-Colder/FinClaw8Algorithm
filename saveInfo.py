import sys
with open("/data/projects/fate/info.txt", 'w+') as f:
    for i in range(len(sys.argv)):
        f.write(sys.argv[i] + "\n")
