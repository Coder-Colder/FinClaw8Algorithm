import sys
with open("/data/projects/fate/info.txt", 'w+') as f:
    f.write(sys.argv[1])
    f.write("\n")
    f.write(sys.argv[2])