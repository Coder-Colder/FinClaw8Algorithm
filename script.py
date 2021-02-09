# Utils
import json
import os
import logging
import re

UPLOAD_JSON_PATH = os.path.join(os.curdir, 'upload_data.json')
PARTIES_PATH = "./parties.conf"
UPLOAD_CONF_PATH = "./upload.conf"
DATA_PATH = os.path.join(os.curdir, 'train_data.csv')

fate_flow_path = "../fate_flow/fate_flow_client.py"
run_task_path = "./run_task_script/run_task.py"
job_conf_path = "./run_task_script/config/test_hetero_linr_train_job_conf.json"
job_dsl_path = "./run_task_script/config/test_hetero_linr_train_job_dsl.json"


# dsl_path = os.path.join(home_dir, "toy_example_dsl.json")
# conf_path = os.path.join(home_dir, "toy_example_conf.json")


def generateTableName(proj_name, cnt):
    list = []
    for i in range(cnt):
        list.append(proj_name + "_" + str(i))
    return list


def create_upload_conf(party_path, party2ip, party2usr, party2pswd, project):
    usernames = []
    passwords = []
    party_list = []
    ip_list = []
    plist = []
    for item in party_path:
        id, path = item
        usernames.append(party2usr[id])
        passwords.append(party2pswd[id])
        party_list.append(id)
        ip_list.append(party2ip[id])
        plist.append(path)
    tlist = generateTableName(project, len(plist))

    with open(UPLOAD_CONF_PATH, "w+") as f:
        f.write("#!/bin/bash\n\n")
        f.write("user=root\n")
        f.write("dir=/data/projects/fate\n")
        f.write("users=({})\n".format(" ".join(usernames)))
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


def create_predict_data_json(model_name, param_dict):
    '''
    创建guest用于预测的json文件,如下：
    {"head":
    {"serviceId":"test"},
    "body":{"featureData":
    {"x0": 0.254879,
    "x1": -1.046633,
    "x2": 0.209656,
    "x3": 0.074214,
    "x4": -0.441366,
    "x5": -0.377645,
    "x6": -0.485934,
    "x7": 0.347072,
    "x8": -0.287570,
    "x9": -0.733474}
    }
    }
    :param model_name:  将要预测的模型名称（在bind时绑定）
    :param param_dict:  用于预测的feature data,为feature name: feature value 的键值对
    :return: json格式的字符串
    '''
    predict_data_json = {}
    predict_data_json["head"] = {}
    predict_data_json["body"] = {}
    predict_data_json["head"]["serviceId"] = model_name
    predict_data_json["body"]["featureData"] = param_dict
    predict_data_str = json.dumps(predict_data_json)
    # print(predict_data_str)
    return predict_data_str


def get_guest_ip(data_path):
    guest_ip = " "
    line = " "
    with open(UPLOAD_CONF_PATH, 'r', encoding='utf-8') as f:
        line = f.readline()
        while line and guest_ip == " ":
            if "partyiplist" in line:
                token = line.split(' ')
                guest_ip = token[0].strip('partyiplist=(').rstrip().rstrip(')')
            line = f.readline()
    f.close()
    return guest_ip


# Argument Parser
import argparse
import os

parser = argparse.ArgumentParser(add_help=True, description="Fedarated Learning command parser")
parser.add_argument("-f", "--function", type=str,
                    choices=["deploy", "delete", "upload", "r_upload", "submit", "load_bind", "predict", "query",
                             "r_query"], required=True,
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

parser.add_argument("-gp", "--guestpair", type=str, nargs=2,
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

parser.add_argument("-mid", "--model_id", type=str,
                    help="the id of the model, needed when submitting the job.Needed when using '-f load_bind'")

parser.add_argument("-mver", "--model_version", type=str,
                    help="the version of the model, needed when submitting the job.Needed when using '-f load_bind'")

parser.add_argument("-mname", "--model_name", type=str,
                    help="a unique name assigned to the model.Needed when using '-f predict' or '-f load_bind'")

parser.add_argument("-params", "--parameters", type=float, nargs="+",
                    help="feature data used to make prediction. Needed when using '-f predict'")

parser.add_argument("-jid", "--jobid", type=str,
                    help="id of job to query on. Needed when using '-f query' or '-f r_query'")

parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

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
    if args.verbose:
        os.system("bash ./generate_config.sh")
        os.system("bash ./docker_deploy.sh all")
    else:
        run_cmd(["bash", "./generate_config.sh"])
        stdout = run_cmd(["bash", "./docker_deploy.sh", "all"])

        '''
        every successful exec will form 2 exits, so test the number of exit 
        '''

        def check_deploy_valid(str):
            pattern = r"(error)|(ERROR)"
            compiled_pattern = re.compile(pattern)
            error_res = compiled_pattern.findall(str)
            return len(error_res) == 0

        if check_deploy_valid(stdout):
            print("deploy success.")
        else:
            print("deploy failure.")


def _upload(datapath, project, tablename):
    create_upload_json(datapath, project, tablename)
    ret = eval(run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH]))
    total_cnt = 20
    i = 0
    while ret["retcode"] != 0 and i < total_cnt:
        if ret["retcode"] == 100:
            ret = eval(run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH, "-drop", "1"]))
        else:
            ret = eval(run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH]))
        i += 1
    print(ret)


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
    party2pswd = {}
    party2usr = {}
    party2ip = {}
    for idx in range(len(idlist)):
        party2ip[idlist[idx]] = iplist[idx]
        party2usr[idlist[idx]] = ulist[idx]
        party2pswd[idlist[idx]] = plist[idx]
    return party2ip, party2usr, party2pswd


def check_valid_retcode(ret_val):
    pattern = "'retcode':\s+([0-9]+),"
    re_exp = re.compile(pattern)
    rets = re_exp.findall(ret_val)
    for val in rets:
        if int(val) != 0:
            return False
    pattern = '''"retcode":\s+([0-9]+),'''
    re_exp = re.compile(pattern)
    rets = re_exp.findall(ret_val)
    for val in rets:
        if int(val) != 0:
            return False
    return True


def upload(guest_pair, host_pair, project):
    if guest_pair is None or len(guest_pair) != 2 or (host_pair is not None and len(host_pair) % 2 != 0):
        print("upload failure.")
    if host_pair is None:
        host_pair = []
    party_path = [(guest_pair[0], guest_pair[1])]
    for idx in range(0, len(host_pair), 2):
        party_path.append((host_pair[idx], host_pair[idx + 1]))
    party2ip, party2usr, party2pswd = getPartyInfo()
    create_upload_conf(party_path, party2ip, party2usr, party2pswd, project)
    if args.verbose:
        os.system("bash ./upload.sh all")
    else:
        stdout = run_cmd(['bash', './upload.sh', 'all'])
        if check_valid_retcode(stdout):
            print("upload success.")
        else:
            print("upload failure.")


def delete(iplist, idlist, passwordlist, users):
    if users == None:
        users = ["root"]
    if len(users) != len(idlist):
        for i in range(len(idlist) - len(users)):
            users.append("root")
    create_parties_json(iplist, idlist, passwordlist, users)
    if args.verbose:
        os.system("bash ./docker_deploy.sh --delete all")
    else:
        run_cmd(["bash", "./docker_deploy.sh", "--delete", "all"])
        print("delete success.")


def submit(alg, proj, work_mode):
    with open(UPLOAD_CONF_PATH, "a+") as f:
        f.write("workmode={}\n".format(work_mode))
    if args.verbose:
        os.system("bash ./upload.sh --submit -m {} -alg {} -proj {}".format(work_mode, alg, proj))
    else:
        stdout = run_cmd("bash ./upload.sh --submit -m {} -alg {} -proj {}".format(work_mode, alg, proj).split(" "))
        info = {}
        if check_valid_retcode(stdout):
            info["retcode"] = 0
            with open("./info.txt", "r") as f:
                f.readline()  # pass the useless params
                info["model_id"] = f.readline().strip("\n")
                info["model_version"] = f.readline().strip("\n")
                info["jobid"] = f.readline().strip("\n")
        else:
            info["retcode"] = 1 # submit failed
        print(info)


def bind(model_name, model_id, model_version):
    if args.verbose:
        os.system("bash ./upload.sh --bind -mid {} -mver {} -mname {}".format(model_id, model_version, model_name))
    else:
        stdout = run_cmd("bash ./upload.sh --bind -mid {} -mver {} -mname {}".format(model_id, model_version, model_name).split(" "))
        if check_valid_retcode(stdout):
            def check_load_bind_valid(str):
                pattern = r"Load model Success"
                compiled_pattern = re.compile(pattern)
                success_res = compiled_pattern.findall(str)
                if len(success_res) == 0:
                    return False
                pattern = r"Bind model Success"
                compiled_pattern = re.compile(pattern)
                success_res = compiled_pattern.findall(str)
                return  len(success_res) != 0

            if check_load_bind_valid(stdout):
                print("load_bind success.")
            else:
                print("load_bind failure.")
        else:
            print("load_bind failure.")


def predict(model_name, params):
    predict_param = {}
    for key, tem in enumerate(params):
        predict_param["x" + str(key)] = tem

    predict_str = create_predict_data_json(model_name, predict_param)
    predict_ip = get_guest_ip(PARTIES_PATH)
    cmd = ("curl -X POST -H 'Content-Type: application/json' -d '" + predict_str +
           "' 'http://" + predict_ip + ":8059/federation/v1/inference'")
    stdout = run_cmd(cmd)
    ret_dict:dict = eval(stdout)
    if "data" in ret_dict.keys():
        print(ret_dict["data"])
    else:
        print(ret_dict)


def _query(jobid):
    ret = run_cmd(["python", fate_flow_path, "-f", "query_job", "-j", jobid])
    ret = json.loads(ret)
    print(ret)
    status = ret["retcode"]
    with open("../info.txt", "w+") as f:
        if status != 0:
            f.write("failed\n")
        else:
            check_data = ret["data"]
            for i in range(len(check_data)):
                f.write(check_data[i]["f_status"] + "\n")

def query(jobid):
    if args.verbose:
        os.system("bash ./upload.sh --query -jobid {}".format(jobid))
    else:
        run_cmd("bash ./upload.sh --query -jobid {}".format(jobid).split(" "))
    ret = ""
    with open("./info.txt", "r") as f:
        for line in f.readlines():
            ret += line
    print(ret, end="")


if args.function == "deploy":
    deploy(args.ip, args.id, args.password, args.users)
elif args.function == "submit":
    submit(args.algorithm, args.project, args.work_mode)
elif args.function == "r_upload":
    _upload(args.datapath, args.project, args.tablename)
elif args.function == "delete":
    delete(args.ip, args.id, args.password, args.users)
elif args.function == "load_bind":
    bind(args.model_name, args.model_id, args.model_version)
elif args.function == "upload":
    upload(args.guestpair, args.hostpair, args.project)
elif args.function == "predict":
    predict(args.model_name, args.parameters)
elif args.function == "query":
    query(args.jobid)
elif args.function == "r_query":
    _query(args.jobid)

