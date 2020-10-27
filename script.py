# Utils
import json
import os
import logging
import paramiko

UPLOAD_JSON_PATH = os.path.join(os.curdir, 'upload_data.json')
PARTIES_PATH = "./parties.conf"
UPLOAD_CONF_PATH = "./upload.conf"
DATA_PATH = os.path.join(os.curdir, 'train_data.csv')

fate_flow_path = "../fate_flow/fate_flow_client.py"
run_task_path = "./run_task_script/run_task.py"
job_conf_path = "./run_task_script/config/test_hetero_linr_train_job_conf.json"
job_dsl_path = "./run_task_script/config/test_hetero_linr_train_job_dsl.json"
#dsl_path = os.path.join(home_dir, "toy_example_dsl.json")
#conf_path = os.path.join(home_dir, "toy_example_conf.json")


def generateTableName(proj_name, cnt):
    list = []
    for i in range(cnt):
        list.append(proj_name + "_" + str(i))
    return list

def create_upload_conf(party_path, party2ip, party2usr, party2pswd, project):
    usernames=[]
    passwords=[]
    party_list=[]
    ip_list=[]
    plist=[]
    for item in party_path:
        id, path = item
        usernames.append(party2usr[id])
        passwords.append(party2pswd[id])
        party_list.append(id)
        ip_list.append(party2ip[id])
        plist.append(path)
    tlist=generateTableName(project, len(plist))

    with open(UPLOAD_CONF_PATH, "w+") as f:
        f.write("#!/bin/bash\n\n")
        f.write("user=root\n")
        f.write("dir=/data/projects/fate\n")
        f.write("users=({})".format(usernames))
        f.write("passwords=({})\n".format(" ".join(passwords)))
        f.write("partylist=({})\n".format(" ".join(party_list)))
        f.write("partyiplist=({})\n".format(" ".join(ip_list)))
        f.write("servingiplist=({})\n".format(" ".join(ip_list)))
        f.write("table_names=({})\n".format(" ".join(tlist)))
        f.write("datapaths=({})\n".format(" ".join(plist)))
        f.write("project={}\n".format(project))

def create_parties_json(ip_list, party_list, passwords, usernames=[]):
    with open(PARTIES_PATH, 'w+') as f:
        f.write('#!/bin/bash\n\n')
        f.write("user=root\n")
        f.write("dir=/data/projects/fate\n")
        f.write("users=({})\n".format(" ".join(usernames)))
        f.write("passwords=({})\n".format(" ".join(passwords)))
        f.write("partylist=({})\n".format(" ".join(party_list)))
        f.write("partyiplist=({})\n".format(" ".join(ip_list)))
        f.write("servingiplist=({})\n".format(" ".join(ip_list)))
        f.write("#exchangeip=\n")
        f.write('''# modify if you are going to use an external db
mysql_ip=mysql
mysql_user=fate
mysql_password=fate_dev
mysql_db=fate_flow

# modify if you are going to use an external redis
redis_ip=redis
redis_port=6379
redis_password=fate_dev''')


# 创建上传数据文件
def create_upload_json(data_path, task_name, table_name: str):
    upload_dict = {}
    upload_dict["head"] = 1
    upload_dict["file"] = data_path
    upload_dict["partition"] = 10
    upload_dict["work_mode"] = 1
    upload_dict["namespace"] = task_name
    upload_dict["table_name"] = table_name
    with open(UPLOAD_JSON_PATH, 'w+') as f:
        json.dump(upload_dict, f, sort_keys=True, indent=4, separators=(', ', ':'))


# Argument Parser
import argparse
import os

parser = argparse.ArgumentParser(add_help=True, description="Fedarated Learning command parser")
parser.add_argument("-f", "--function", type=str, choices=["deploy", "upload", "submit", "delete", "load_bind", "predict", "r_upload"], required=True,
                    help="choose the function to execute.")

parser.add_argument("-u", "--users", type=str, nargs='*',
                    help="username for logging in destination host, default--root.The first username will be regarded \
                    as the user on regulator host. Need to specify when using '-f deploy'.")

parser.add_argument("-pw", "--password", type=str, nargs='+',
                    help="password for each user respectively.The first password will be regarded \
                    as the password for logging in regulator host. Need to specify when using '-f deploy'.")

parser.add_argument("-id", "--id", type=str, nargs='+',
                    help="party id assigned to each host respectively.The first id will be regarded \
                    as the id assigned to regulator host. Need to specify when using '-f deploy'.")

parser.add_argument("-ip", "--ip", type=str, nargs='+',
                    help="ipv4 address of each host respectively.The first ip will be regarded \
                    as the ip of regulator host. Need to specify when using '-f deploy'.")

parser.add_argument("-gp", "--guestpair", type=str,
                    help="Needed when using '-f upload")

parser.add_argument("-hp", "--hostpair", type=str, nargs="+",
                    help="Needed when using '-f upload'")

parser.add_argument("-proj", "--project", type=str,
                    help="name of the training project. Need to specify when using '-f deploy' or '-f r_upload'\
                     or '-f upload'.")

parser.add_argument("-dp", "--datapath", type=str,
                    help="path of dataset to upload on local host. Need to specify when using '-f r_upload'")

parser.add_argument("-tb", "--tablename", type=str,
                    help="name of data table to configure upload.json. Need to specify when using '-f r_upload'")

parser.add_argument("-alg", "--algorithm", type=str, choices=["hetero_lr", "hetero_linr", "example"],
                    help="configure the Machine Learning Algorithm.")

parser.add_argument("-m", "--work_mode", type=int, choices=[0, 1],
                    help="the mode of the work, 0 means stand-alone deployment and 1 means multiple deployment,\
                     needed when using'-f submit'.")

parser.add_argument("-mid", "--model_id", type=int,
                    help="the id of the model, needed when submitting the job.Needed when using '-f load_bind'")

parser.add_argument("-mver", "--model_version", type=int,
                    help="the version of the model, needed when submitting the job.Needed when using '-f load_bind'")

parser.add_argument("-mname", "--model_name", type=str,
                    help="a unique name assigned to the model.Needed when using '-f predict' or '-f load_bind'")

parser.add_argument("-params", "--parameters", type=float, nargs="+",
                    help="feature data used to make prediction. Needed when using '-f predict'")

args = parser.parse_args()


import subprocess


def run_cmd(cmd):
    logging.info(f"cmd: {' '.join(cmd)}")
    subp = subprocess.Popen(cmd,
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    subp.wait()
    stdout, stderr = subp.communicate()
    return stdout.decode("utf-8")


def deploy(iplist, idlist, passwordlist, users):
    if users == None:
        users = ["root"]
    if len(users) != len(idlist):
        for i in range(len(idlist) - len(users)):
            users.append("root")
    create_parties_json(iplist, idlist, passwordlist, users)
    run_cmd(["bash", "./generate_config.sh"])
    run_cmd(["bash", "./docker_deploy.sh", "all"])
    print("success")


def _upload(datapath, project, tablename):
    create_upload_json(datapath, project, tablename)
    ret = eval(run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH]))
    total_cnt = 20
    i = 0
    while ret["retcode"] != 0 and i < total_cnt:
        ret = eval(run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH]))
        i += 1


def getPartyInfo():
    with open("./parties.conf", "r+", encoding="utf-8") as f:
        for line in f.readlines():
            if line.find("partyiplist") != -1:
                iplist = line.strip("\n").strip("partyiplist=").strip("(").strip(")").split(" ")
            elif line.find("users") != -1:
                ulist = line.strip("\n").strip("users=").strip("(").strip(")").split(" ")
            elif line.find("passwords") != -1:
                plist = line.strip("\n").strip("passwords=").strip("(").strip(")").split(" ")
            elif line.find("partylist") != -1:
                idlist = line.strip("\n").strip("partylist=").strip("(").strip(")").split(" ")
    party2pswd={}
    party2usr={}
    party2ip={}
    for idx in range(len(idlist)):
        party2ip[idlist[idx]] = iplist[idx]
        party2usr[idlist[idx]] = ulist[idx]
        party2pswd[idlist[idx]] = plist[idx]
    return party2ip, party2usr, party2pswd


def upload(guest_pair, host_pair, project):
    if guest_pair is None or len(guest_pair) != 2 or (host_pair is not None and len(host_pair) % 2 != 0):
        print("error!")
    if host_pair is None:
        host_pair = []
    party_path = [(guest_pair[0], guest_pair[1])]
    for idx in range(0, len(host_pair), 2):
        party_path.append((host_pair[idx], host_pair[idx+1]))
    party2ip, party2usr, party2pswd = getPartyInfo()
    create_upload_conf(party_path, party2ip, party2usr, party2pswd, project)
    os.system("bash ./upload.sh")


def delete():
    run_cmd(["bash", "./docker_deploy.sh", "--delete", "all"])


def submit(alg, proj, work_mode):
    os.system("bash ./upload.sh --submit -m {} -alg {} -proj {}".format(work_mode, alg, proj))


def bind(model_name, model_id, model_version):
    pass


def predict(model_name, params):
    pass



if args.function == "deploy":
    deploy(args.ip, args.id, args.password, args.users)
elif args.function == "submit":
    submit(args.algorithm, args.project, args.work_mode)
elif args.function == "r_upload":
    _upload(args.datapath, args.project, args.tablename)
elif args.function == "delete":
    delete()
elif args.function == "bind":
    bind(args.model_name, args.model_id, args.model_version)
elif args.function == "upload":
    upload(args.guestpair, args.hostpair, args.project)
elif args.function == "predict":
    predict(args.model_name, args.parameters)
