# Copyright 2019-2020 VMware, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# you may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash

BASEDIR=$(dirname "$0")
cd $BASEDIR
WORKINGDIR=$(pwd)
password=0
datapath=0
table_name=0
timecnt=300

# fetch fate-python image
source ${WORKINGDIR}/.env
source ${WORKINGDIR}/upload.conf

cd ${WORKINGDIR}

Upload() {
    iii=0
	for party in ${partylist[*]}; do
		password=${passwords[iii]}
		datapath=${datapaths[iii]}
		table_name=${table_names[iii]}
		((iii++))
		PartyUpload $party
	done
}

PartyUpload() {
    target_party_id=$1
	# should not use localhost at any case
	target_ip="127.0.0.1"

	# check configuration files
	if [ ! -f ${WORKINGDIR}/script.py ]; then
		echo "Unable to find file script.py, please generate it first."
		exit 1
	fi
	# extract the ip address of the target party
	for ((i = 0; i < ${#partylist[*]}; i++)); do
		if [ "${partylist[$i]}" = "$target_party_id" ]; then
			target_ip=${partyiplist[$i]}
		fi
	done
	# verify the target_party_ip
	if [ "$target_ip" = "127.0.0.1" ]; then
		echo "Unable to find Party : $target_party_id serving address, please check you input."
		exit 1
	fi

/usr/bin/expect <<EOF
    set timeout $timecnt
	spawn scp ${WORKINGDIR}/script.py $user@$target_ip:~/
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect eof
EOF

/usr/bin/expect<<EOF
    set timeout $timecnt
    spawn ssh $user@$target_ip
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect "#"
	send "ls\r"
    expect "#"
    send "docker exec -it confs-${target_party_id}_python_1 bash\r"
    expect "#"
    send "mkdir -p $project\r"
    expect "#"
    send "exit\r"
	expect "#"
	send "docker cp $datapath confs-${target_party_id}_python_1:/data/projects/fate/python/${project}/data.csv\r"
	expect "#"
	send "docker cp ~/script.py confs-${target_party_id}_python_1:/data/projects/fate/python/${project}/\r"
    expect "#"
	send "rm ~/script.py\r"
    expect "#"
    send "docker exec -it confs-${target_party_id}_python_1 bash\r"
    expect "#"
    send "cd ${project}\r"
    expect "#"
    send "python script.py -f r_upload -tb $table_name -dp /data/projects/fate/python/${project}/data.csv -proj $project\r"
    expect {
		"success" {
			expect "#"
			send "exit\r"
		}
		"#" {
			send "exit\r"
		}
	}
	expect "#"
    send "exit\r"
    expect eof
EOF
    echo "party $target_party_id upload dataset is ok!"
}

ShowUsage() {
	echo "Usage: "
	echo "Deploy all parties or specified partie(s): bash docker_deploy.sh partyid1[partyid2...] | all"
}

Submit() {
	work_mode=$3
	alg=$5
	project=$7
	tables=${table_names}
	gid=${partylist[0]}
	hid=${partylist[@]:1:${#partylist[*]}-1}
	target_party_ip=${partyiplist[0]}
	password=${passwords[0]}
/usr/bin/expect<<EOF
    set timeout $timecnt
    spawn scp -r ${WORKINGDIR}/run_task_script $user@$target_party_ip:~/
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect eof
EOF
/usr/bin/expect<<EOF
    set timeout $timecnt
	spawn scp ${WORKINGDIR}/saveInfo.py $user@$target_party_ip:~/
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect eof
EOF

/usr/bin/expect<<EOF
    set timeout $timecnt
    spawn ssh $user@$target_party_ip
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect "#"
	send "docker cp ~/run_task_script confs-${gid}_python_1:/data/projects/fate/python/${project}/run_task_script\r"
	expect "#"
	send "docker cp ~/saveInfo.py confs-${gid}_python_1:/data/projects/fate/\r"
	expect "#"
	send "rm -rf ~/run_task_script\r"
	expect "#"
	send "rm -rf ~/saveInfo.py\r"
	expect "#"
	send "docker exec -it confs-${gid}_python_1 bash\r"
	expect "#"
	send "cd ${project}/\r"
	expect "#"
	send "python ./run_task_script/run_task.py -m ${work_mode} -alg ${alg} -proj ${project} -t ${tables} -gid ${gid} -hid ${hid} -aid ${gid}\r"
    expect {
		"success" {
			expect "#"
			send "exit\r"
		}
		"#" {
			send "exit\r"
		}
	}
	expect "#"
    send "exit\r"
    expect eof
EOF
/usr/bin/expect<<EOF
    set timeout $timecnt
    spawn ssh $user@$target_party_ip
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect "#"
	send "docker cp confs-${gid}_python_1:/data/projects/fate/info.txt ~/info.txt\r"
	expect "#"
    send "exit\r"
    expect eof
EOF
/usr/bin/expect<<EOF
    set timeout $timecnt
	spawn scp $user@$target_party_ip:~/info.txt ${WORKINGDIR}/
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect eof
EOF
}

Bind() {
	work_mode=$workmode
	alg=xxx
	proj=xxx
	model_id=${3}
	model_version=${5}
	model_name=${7}
	gid=${partylist[0]}
	hid=${partylist[@]:1:${#partylist[*]}-1}
	table_name=xxx
	target_party_ip=${partyiplist[0]}
	password=${passwords[0]}
/usr/bin/expect<<EOF
    spawn ssh $user@$target_party_ip
	expect {
		"(yes/no)?" {
			send "yes\n"
			expect "password:"
			send "$password\n"
		}
		"password:" {
			send "$password\n"
		}
	}
	expect "#"
	send "docker exec -it confs-${gid}_python_1 bash\r"
	expect "#"
	send "cd ${project}/\r"
	expect "#"
	send "python ./run_task_script/run_task.py -m ${work_mode} -s 1 -alg ${alg} -proj ${proj} -t ${table_name} -mid ${model_id} -mv ${model_version} -gid ${gid} -hid ${hid} -aid ${gid}\r"
    expect {
		"success" {
			expect "#"
			send "exit\r"
		}
		"#" {
			send "exit\r"
		}
	}
    expect "#"
    send "exit\r"
    expect eof
EOF
}

main() {
	if [ "$1" = "" ] || [ "$" = "--help" ]; then
		ShowUsage
		exit 1
	elif [ "$1" = "--submit" ]; then
		Submit "$@"
	elif [ "$1" = "--bind" ]; then
		Bind "$@"
	else
		Upload "$@"
	fi

	exit 0
}

main $@