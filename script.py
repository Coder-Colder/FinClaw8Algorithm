# Utils
import json
import os
import logging

UPLOAD_JSON_PATH = os.path.join(os.curdir, 'upload_data.json')
PARTIES_PATH = "./parties.conf"
DATA_PATH = os.path.join(os.curdir, 'train_data.csv')

fate_flow_path = "../fate_flow/fate_flow_client.py"
#dsl_path = os.path.join(home_dir, "toy_example_dsl.json")
#conf_path = os.path.join(home_dir, "toy_example_conf.json")


def generateTableName(proj_name, cnt):
    list = []
    for i in range(cnt):
        list.append(proj_name + "_" + str(i))
    return list


def create_parties_json(proj_name, ip_list, party_list, passwords, datapaths, usernames=[]):
    with open(PARTIES_PATH, 'w+') as f:
        f.write('#!/bin/bash\n\n')
        f.write("project={}\n".format(proj_name))
        f.write("user=root\n")
        f.write("dir=/data/projects/fate\n")
        f.write("users=({})\n".format(" ".join(usernames)))
        f.write("datapaths=({})\n".format(" ".join(datapaths)))
        f.write("passwords=({})\n".format(" ".join(passwords)))
        f.write("partylist=({})\n".format(" ".join(party_list)))
        f.write("partyiplist=({})\n".format(" ".join(ip_list)))
        f.write("servingiplist=({})\n".format(" ".join(ip_list)))
        f.write("table_names=({})\n".format(" ".join(generateTableName(proj_name, len(ip_list)))))
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
    f.close()


# 创建上传数据文件
def create_upload_json(data_path, task_name, table_name: str):
    upload_dict = {}
    upload_dict["head"] = 1
    upload_dict["file"] = data_path
    upload_dict["partition"] = 10
    upload_dict["work_mode"] = 1
    upload_dict["namespace"] = task_name
    upload_dict["table_name"] = table_name
    with open(UPLOAD_JSON_PATH, 'w') as f:
        json.dump(upload_dict, f, sort_keys=True, indent=4, separators=(', ', ':'))
    f.close()


# Argument Parser
import argparse
import os

parser = argparse.ArgumentParser(add_help=True, description="Fedarated Learning command parser")
parser.add_argument("-f", "--function", type=str, choices=["deploy", "upload", "submit", "delete"], required=True,
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

parser.add_argument("-p", "--path", type=str, nargs='+', metavar='dataPath',
                    help="path of dataset(.csv file) on each host respectively. The first path will be regarded \
as path of dataset on regulator host. Need to specify when using '-f deploy'.")

parser.add_argument("-proj", "--project", type=str,
                    help="name of the training project. Need to specify when using '-f deploy' or '-f upload'.")

parser.add_argument("-dp", "--datapath", type=str,
                    help="path of dataset to upload on local host. Need to specify when using '-f upload'")

parser.add_argument("-tb", "--tablename", type=str,
                    help="name of data table to configure upload.json. Need to specify when using '-f upload'")

parser.add_argument("-alg", "--algorithm", type=str, choices=["SecureBoost"],
                    help="configure the Machine Learning Algorithm.")

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


def deploy():
    if args.users == None:
        users = ["root"]
    else:
        users = args.users
    create_parties_json(args.project, args.ip, args.id, args.password, args.path, users)
    os.system("bash ./generate_config.sh")
    os.system("bash ./docker_deploy.sh all")


def upload():
    create_upload_json(args.datapath, args.project, args.tablename)
    ret = run_cmd(["python", fate_flow_path, "-f", "upload", "-c", UPLOAD_JSON_PATH])
    print(ret)


def delete():
    os.system("bash ./docker_deploy.sh --delete all")

def submit():
    pass


if args.function == "deploy":
    deploy()
elif args.function == "submit":
    submit()
elif args.function == "upload":
    upload()
