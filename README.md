# 1.运行环境

监管方环境要求

1. 可联网的Linux主机
2. Docker: 18+
3. Docker-Compose: 1.24+
4. 部署了kubefate-1.4.4

​	部署方式如下：

```
#新建项目目录
mkdir -p kubefate

cd kubefate

#下载 kubefate-docker-compose-1.4.4
wget  https://github.com/FederatedAI/KubeFATE/releases/download/v1.4.4/kubefate-docker-compose-1.4.4.tar.gz

#解压到当前文件夹
tar -zxvf kubefate-docker-compose-1.4.4.tar.gz ./

rm kubefate-docker-compose-1.4.4.tar.gz

#下载fate-1.4.4镜像(下载过程可能会有些慢)
wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/fate_1.4.4-images.tar.gz 

#加载镜像
docker load -i fate_1.4.4-images.tar.gz
```

部署完成后，将算法组脚本文件`script.py`和`docker_deploy.sh`拷贝至前述解压得到的目录`docker-deploy`下，直接替换掉原目录中的`docker_deploy.sh`文件



# 2.接口说明

1. 所有接口通过命令运行脚本并传入指定参数完成调用，脚本文件将自动解析参数并完成指定任务，返回值或出错信息直接输出到标准输出中，调用者可以通过读取标准输出或者重定向方式获取。

2. 所有功能都通过运行脚本script.py完成，其使用方法参数含义为

   ```
   usage: python3 script.py [-h] 
                    -f {deploy,submit,delete}
   				 [-u [USERS [USERS ...]]] 
                    [-pw PASSWORD [PASSWORD ...]]
                    [-id ID [ID ...]] [-ip IP [IP ...]]
                    [-p dataPath [dataPath ...]] 
                    [-proj PROJECT]
                    [-alg {SecureBoost}]
   
   optional arguments:
   -h, --help              show this help message and exit
   -f {deploy, submit,delete}, --function {deploy, submit,delete}
                           指明脚本需要完成的任务，支持选项为deploy,submit,delte
   -u [USERS [USERS ...]], --users [USERS [USERS ...]]
                           该命令暂时无效，默认使用root用户
   -pw PASSWORD [PASSWORD ...], --password PASSWORD [PASSWORD ...]
                           各方（参与方和监管方）主机上用户的密码，默认给出的第一个密码为监管方主机上的用户
   -id ID [ID ...], --id ID [ID ...]
                           系统为参与训练任务的各方指定的全局唯一id,默认给出第一个id为监管方的id
   -ip IP [IP ...], --ip IP [IP ...]
                           参与训练任务的各方主机的ipv4地址,默认给出的第一个ip为监管方的ip
   -p dataPath [dataPath ...], --path dataPath [dataPath ...]
                           参与训练任务的各方主机上的数据集路径（绝对路径）, 默认给出的第一个dataPath为监管方主机上的数据集路径
   -proj PROJECT, --project PROJECT
                           本次训练任务的名字
   -alg {SecureBoost}, --algorithm {SecureBoost}
                           配置使用的机器学习算法，支持选项：
   ```

3. 特别说明：

   1. `-u`/`--users` 参数暂时无效，请给出参与训练各方的root用户的密码
   2. 每次执行脚本必须给出`-f`/`--function`参数，用于指明此次调用脚本需要完成的任务。可选任务说明：
      + `deploy`:完成在参与训练的各方主机上部署训练环境，并上传数据集。执行该任务前需要满足以下要求
        1. 参与训练的各方主机上应已经将数据集存放在所给路径下
        2. 当任务指明为`deploy`时，必须明确给出参数`-pw`, `-id`, `-ip`, `-p`, `-proj`，每个参数都是长度一致的列表，注意元素的对应性
      + `submit`：必须在`deploy`完成后才能执行，功能：在训练环境部署完成的前提下由监管方发起一次训练任务
        1. 该任务执行成功会返回模型id和version，用于后续绑定模型和开展预测服务，需要保存
        2. 该任务执行失败会返回错误码和错误内容
        3. 当任务指明为`submit`时，必须明确给出参数`-alg`，`-proj`
        4. `deploy`任务和`submit`任务有继承性关联，一般`deploy`任务后紧跟`submit`，若多次`deploy`后才调用`subit`则会以最后一次`deploy`部署的节点和提交数据集开展训练。请勿多次调用`submit`，否则将提交多次相同的训练任务，造成不必要的开销
      + `delete`：删除之前的部署，不需要给出其余配置信息，默认使用上一次deploy的配置

4. 示例

   + `deploy`

     ```
     python3 script.py -f deploy -pw 123456 123456 -id 1 2 -ip 1.1.1.1 2.2.2.2 -p /home/user/data/train.csv /root/train.csv -proj example
     ```

   + `submit`:
   
     ```
     python3 script.py -f submit -alg SecureBoost -proj example
     ```
   
   + `delete`：
   
     ```
     python3 script.py -f delete
     ```
   
     

