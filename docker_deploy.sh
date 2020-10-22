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

# fetch fate-python image
source ${WORKINGDIR}/.env
source ${WORKINGDIR}/parties.conf

cd ${WORKINGDIR}

Deploy() {
	if [ "$1" = "" ]; then
		echo "No party id was provided, please check your arguments "
		exit 1
	fi

	while [ "$1" != "" ]; do
		case $1 in
		splitting_proxy)
			shift
			DeployPartyInternal $@
			break
			;;
		all)
			iii=0
			for party in ${partylist[*]}; do
				password=${passwords[iii]}
				datapath=${datapaths[iii]}
				table_name=${table_names[iii]}
				((iii++))
				if [ "$2" != "" ]; then
					case $2 in
					--training)
						DeployPartyInternal $party
						if [ "${exchangeip}" != "" ]; then
							DeployPartyInternal exchange
						fi
						;;
					--serving)
						DeployPartyServing $party
						;;
					esac
				else
					DeployPartyInternal $party
					DeployPartyServing $party
					if [ "${exchangeip}" != "" ]; then
						DeployPartyInternal exchange
					fi
				fi
			done
			break
			;;
		*)
			if [ "$2" != "" ]; then
				case $2 in
				--training)
					DeployPartyInternal $1
					break
					;;
				--serving)
					DeployPartyServing $1
					break
					;;
				esac
			else
				DeployPartyInternal $1
				DeployPartyServing $1
			fi
			;;
		esac
		shift

	done
}

Delete() {
	if [ "$1" = "" ]; then
		echo "No party id was provided, please check your arguments "
		exit 1
	fi

	while [ "$1" != "" ]; do
		case $1 in
		all)
			iii=0
			for party in ${partylist[*]}; do
				password=${passwords[iii]}
				datapath=${datapaths[iii]}
				table_name=${table_names[iii]}
				((iii++))
				if [ "$2" != "" ]; then
					DeleteCluster $party $2
				else
					DeleteCluster $party
				fi
			done
			if [ "${exchangeip}" != "" ]; then
				DeleteCluster exchange
			fi
			break
			;;
		*)
			DeleteCluster $@
			break
			;;
		esac
	done
}

DeployPartyInternal() {
	target_party_id=$1
	# should not use localhost at any case
	target_party_ip="127.0.0.1"

	# check configuration files
	if [ ! -d ${WORKINGDIR}/outputs ]; then
		echo "Unable to find outputs dir, please generate config files first."
		exit 1
	fi
	if [ ! -f ${WORKINGDIR}/outputs/confs-${target_party_id}.tar ]; then
		echo "Unable to find deployment file for party $target_party_id, please generate it first."
		exit 1
	fi
	# extract the ip address of the target party
	if [ "$target_party_id" = "exchange" ]; then
		target_party_ip=${exchangeip}
	elif [ "$2" != "" ]; then
		target_party_ip="$2"
	else
		for ((i = 0; i < ${#partylist[*]}; i++)); do
			if [ "${partylist[$i]}" = "$target_party_id" ]; then
				target_party_ip=${partyiplist[$i]}
			fi
		done
	fi
	# verify the target_party_ip
	if [ "$target_party_ip" = "127.0.0.1" ]; then
		echo "Unable to find Party: $target_party_id, please check you input."
		exit 1
	fi

	if [ "$3" != "" ]; then
		user=$3
	fi

	#scp ${WORKINGDIR}/outputs/confs-$target_party_id.tar $user@$target_party_ip:~/
	#rm -f ${WORKINGDIR}/outputs/confs-$target_party_id.tar
	#echo "$target_party_ip training cluster copy is ok!"
	#ssh -tt $user@$target_party_ip <<eeooff

/usr/bin/expect <<EOF
	spawn scp ${WORKINGDIR}/outputs/confs-$target_party_id.tar $user@$target_party_ip:~/
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

/usr/bin/expect <<EOF
	spawn scp ${WORKINGDIR}/script.py $user@$target_party_ip:~/
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

	echo "$target_party_ip training cluster copy is ok!"

/usr/bin/expect <<EOF
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
	send "ls\r"
	expect "#"
	send "mkdir -p $dir\r"
	expect "#"
	send "rm -f $dir/confs-$target_party_id.tar\r"
	expect "#"
	send "mv ~/confs-$target_party_id.tar $dir\r"
	expect "#"
	send "cd $dir\r"
	expect "#"
	send "tar -xzf confs-$target_party_id.tar\r"
	expect "#"
	send "cd confs-$target_party_id\r"
	expect "#"
	send "docker-compose down\r"
	expect "#"
	send "docker volume rm -f confs-${target_party_id}_shared_dir_examples\r"
	expect "#"
	send "docker volume rm -f confs-${target_party_id}_shared_dir_federatedml\r"
	expect "#"
	send "docker-compose up -d\r"
	expect "#"
	send "rm -f ../confs-${target_party_id}.tar\r"
	expect "#"
	send "docker-compose up -d\r"
    expect "#"
	send "exit\r"
	expect eof
EOF
/usr/bin/expect <<EOF
	spawn ssh $user@$target_party_serving_ip
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
	send "cd $dir\r"
	expect "#"
	send "cd confs-$target_party_id\r"
	expect "#"
	send "docker-compose up -d\r"
	expect "#"
    send "exit\r"
EOF
	echo "party ${target_party_id} deploy is ok!"
}

DeployPartyServing() {
	target_party_id=$1
	# should not use localhost at any case
	target_party_serving_ip="127.0.0.1"

	# check configuration files
	if [ ! -d ${WORKINGDIR}/outputs ]; then
		echo "Unable to find outputs dir, please generate config files first."
		exit 1
	fi
	if [ ! -f ${WORKINGDIR}/outputs/serving-${target_party_id}.tar ]; then
		echo "Unable to find deployment file for party $target_party_id, please generate it first."
		exit 1
	fi
	# extract the ip address of the target party
	for ((i = 0; i < ${#partylist[*]}; i++)); do
		if [ "${partylist[$i]}" = "$target_party_id" ]; then
			target_party_serving_ip=${servingiplist[$i]}
		fi
	done
	# verify the target_party_ip
	if [ "$target_party_serving_ip" = "127.0.0.1" ]; then
		echo "Unable to find Party : $target_party_id serving address, please check you input."
		exit 1
	fi

	#scp ${WORKINGDIR}/outputs/serving-$target_party_id.tar $user@$target_party_serving_ip:~/
	#echo "party $target_party_id serving cluster copy is ok!"
	#ssh -tt $user@$target_party_serving_ip <<eeooff
/usr/bin/expect <<EOF
	spawn scp ${WORKINGDIR}/outputs/serving-$target_party_id.tar $user@$target_party_serving_ip:~/
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
	echo "party $target_party_id serving cluster copy is ok!"

/usr/bin/expect <<EOF
	spawn ssh $user@$target_party_serving_ip
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
	send "mkdir -p $dir\r"
	expect "#"
	send "rm -f $dir/serving-$target_party_id.tar\r"
	expect "#"
	send "mv ~/serving-$target_party_id.tar $dir\r"
	expect "#"
	send "cd $dir\r"
	expect "#"
	send "tar -xzf serving-$target_party_id.tar\r"
	expect "#"
	send "cd serving-$target_party_id\r"
	expect "#"
	send "docker-compose down\r"
	expect "#"
	send "docker-compose up -d\r"
	expect "#"
	send "rm -f ../serving-$target_party_id.tar\r"
	expect "#"
	send "docker-compose up -d\r"
	expect "#"
    send "exit\r"
EOF
/usr/bin/expect <<EOF
	spawn ssh $user@$target_party_serving_ip
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
	send "cd $dir\r"
	expect "#"
	send "cd serving-$target_party_id\r"
	expect "#"
	send "docker-compose up -d\r"
	expect "#"
    send "exit\r"
EOF
	echo "party $target_party_id serving cluster deploy is ok!"

/usr/bin/expect<<EOF
    spawn ssh $user@$target_party_serving_ip
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
	send "docker ps\r"
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
    send "docker exec -it confs-${target_party_id}_python_1 bash\r"
    expect "#"
    send "cd ${project}\r"
    expect "#"
    send "python3 script.py -f upload -tb $table_name -proj $project -dp /data/projects/fate/python/${project}/data.csv\r"
    expect "#"
    send "exit\r"
	expect "#"
	send "rm ~/script.py\r"
	expect "#"
EOF
    echo "party $target_party_id upload dataset is ok!"
}

DeleteCluster() {
	target_party_id=$1
	cluster_type=$2
	target_party_serving_ip="127.0.0.1"
	target_party_ip="127.0.0.1"

	# extract the ip address of the target party
	if [ "$target_party_id" == "exchange" ]; then
		target_party_ip=${exchangeip}
	else
		for ((i = 0; i < ${#partylist[*]}; i++)); do
			if [ "${partylist[$i]}" = "$target_party_id" ]; then
				target_party_ip=${partyiplist[$i]}
			fi
		done
	fi

	for ((i = 0; i < ${#partylist[*]}; i++)); do
		if [ "${partylist[$i]}" = "$target_party_id" ]; then
			target_party_serving_ip=${servingiplist[$i]}
		fi
	done

	# delete training cluster
	if [ "$cluster_type" == "--training" ]; then
/usr/bin/expect <<EOF
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
		send "cd $dir/confs-$target_party_id\r"
		expect "#"
		send "docker-compose down\r"
		expect "#"
		send "exit\r"
		expect eof
EOF
		#ssh -tt $user@$target_party_ip 
		echo "party $target_party_id training cluster is deleted!"
	# delete serving cluster
	elif [ "$cluster_type" == "--serving" ]; then
/usr/bin/expect <<EOF
		spawn ssh $user@$target_party_serving_ip
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
		send "cd $dir/serving-$target_party_id\r"
		expect "#"
		send "docker-compose down\r"
		expect "#"
		send "exit\r"
		expect eof
EOF
		#ssh -tt $user@$target_party_serving_ip 
		echo "party $target_party_id serving cluster is deleted!"
	# delete training cluster and serving cluster
	else
		# if party is exchange then delete exchange cluster
		if [ "$target_party_id" == "exchange" ]; then
/usr/bin/expect <<EOF
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
		send "cd $dir/confs-$target_party_id\r"
		expect "#"
		send "docker-compose down\r"
		expect "#"
		send "exit\r"
		expect eof
EOF
			#ssh -tt $user@$target_party_ip 
		else
/usr/bin/expect <<EOF
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
		send "cd $dir/confs-$target_party_id\r"
		expect "#"
		send "docker-compose down\r"
		expect "#"
		send "exit\r"
		expect eof
EOF
			#ssh -tt $user@$target_party_ip 
			echo "party $target_party_id training cluster is deleted!"
/usr/bin/expect <<EOF
			spawn ssh $user@$target_party_serving_ip
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
			send "cd $dir/serving-$target_party_id\r"
			expect "#"
			send "docker-compose down\r"
			expect "#"
			send "exit\r"
			expect eof
EOF
			#ssh -tt $user@$target_party_serving_ip 
			echo "party $target_party_id serving cluster is deleted!"
		fi
	fi
}

ShowUsage() {
	echo "Usage: "
	echo "Deploy all parties or specified partie(s): bash docker_deploy.sh partyid1[partyid2...] | all"
}

main() {
	if [ "$1" = "" ] || [ "$" = "--help" ]; then
		ShowUsage
		exit 1
	elif [ "$1" = "--delete" ] || [ "$1" = "--del" ]; then
		shift
		Delete $@
	else
		Deploy "$@"
	fi

	exit 0
}

main $@
