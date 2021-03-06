# 1.运行环境

监管方环境要求

1. 可联网的Linux主机
2. Docker: 18+
3. Docker-Compose: 1.24+
4. 部署了kubefate-1.4.4
5. 安装expect

部署方式如下：

```
#安装expect
sudo apt-get install expect

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

#配置ssh root用户登陆
将/etc/ssh/sshd_config中的 PemitRootLogin no/without-password 改为 PermitRootLogin yes
```

部署完成后，将本仓库中所有文件拷贝至前述解压得到的目录`docker-deploy`下，直接替换掉原目录中的重名文件



# 2.接口说明

1. 所有接口通过命令运行脚本并传入指定参数完成调用，脚本文件将自动解析参数并完成指定任务，返回值或出错信息直接输出到标准输出中，调用者可以通过读取标准输出或者重定向方式获取。

2. 所有功能都通过运行脚本script.py完成，其使用方法参数含义为

   ```
   usage: python3 script.py [-h] 
                    -f {deploy,submit,delete,upload,query,load_bind, predict}
                    [-u [USERS [USERS ...]]] 
                    [-pw PASSWORD [PASSWORD ...]]
                    [-id ID [ID ...]] [-ip IP [IP ...]]
                    [-gp guestpair]
                    [-hp hostpair [hostpair ...]] 
                    [-proj PROJECT]
                    [-alg {hetero_lr, hetero_linr, example}]
                    [-m  work mode]
                    [-mid model_id]
                    [-mver model_version]
                    [-mname model_name]
                    [-params param [param ...]]
                    [-jid jobid]
   
   optional arguments:
   -h, --help              show this help message and exit
   -f {deploy,submit,delete,upload,query,load_bind, predict},
                           指明脚本需要完成的任务，支持选项为deploy,submit,delete,upload,query,load_bind, predict
   -u [USERS [USERS ...]], --users [USERS [USERS ...]]
                           该命令暂时无效，默认使用root用户，deploy时使用
   -pw PASSWORD [PASSWORD ...], --password PASSWORD [PASSWORD ...]
                           各方（参与方和监管方）主机上用户的密码，deploy时使用
   -id ID [ID ...], --id ID [ID ...]
                           系统为参与训练任务的各方指定的全局唯一id, deploy时使用
   -ip IP [IP ...], --ip IP [IP ...]
                           参与训练任务的各方主机的ipv4地址, deploy时使用
   -gp guest pair 
                           训练任务中的guest方id（拥有标签的一方）与数据集路径（绝对路径）组成的二元组，只有一个，upload时使用
   -hp host pair [host pair ...]
                           训练任务中的host方id(没有标签的其余合作方）与数据集路径（绝对路径）组成的二元组序列，一个列表，upload时使用
   -proj PROJECT, --project PROJECT
                           本次训练任务的名字， upload和submit时使用
   -alg {hetero_lr, hetero_linr, example}, --algorithm {hetero_lr, hetero_linr, example}
                           配置使用的机器学习算法，支持选项：hetero_lr, hetero_linr, example.其中example为最简单的加法同态加密测试
   -m {0,1}
                           模型训练模式，1为多主机，0为单机
   -mid model_id
                           模型id
   -mver model_version
                           模型版本
   -mname model_name
                           模型命名
   -params param [param ...]
                           预测使用的特征数据
   -jid jobid
                           查询训练任务状态使用的jobid
   ```

3. 特别说明：

   1. `-u`/`--users` 参数暂时无效，请给出参与训练各方的root用户的密码
   2. 每次执行脚本必须给出`-f`/`--function`参数，用于指明此次调用脚本需要完成的任务。可选任务说明：
      + `deploy`:完成在参与训练的各方主机上部署训练环境执行该任务前需要满足以下要求

        1. 当任务指明为`deploy`时，必须明确给出参数`-pw`, `-id`, `-ip`，每个参数都是长度一致的列表，注意元素的对应性

        2. 返回值-单行字符串

           + 成功：`deploy success.`

           + 失败: `deploy failure.`

      + `upload`:必须在`deploy`完成后执行，功能：完成各参与方数据集上传
        
        1. 参与训练的各方主机上应已经将数据集存放在所给路径下
        
        2. 当任务指明为`upload`时，必须明确给出参数`-gp`,`-hp`, `-proj`
        
        3. `-gp`和`-hp`参数都是合作方id与其主机上数据集路径的二元组，`-gp`只接受一个二元组，`-hp`可接受一个二元组序列。
        
        4. 注：第3点终说明的二元组（id, path）在传参时并不需要明确用括号和逗号标识，直接以`id path`形式给出，例如
            ```
            python script.py -gp 9999 /root/data.csv -hp 9999 /root/data1.csv 10000 /root/data2.csv
            ```
            含义为id为9999的一方同时扮演角色guest和host，分别要上传数据集/root/data.csv和/root/data1.csv，而id为10000的一方扮演角色host, 上传数据集为/root/data2.csv
            
        5. `upload`任务和`deploy`任务有继承性关联，一般`deloy`任务后紧跟`upload`，不应穿插其他任务
        
        6. 返回值-单行字符串
        
            + 成功：`upload success.`
        
            + 失败: `upload failure.`
        
      + `submit`：必须在`upload`完成后才能执行，功能：在训练环境部署完成的前提下由监管方发起一次训练任务

        1. 该任务执行失败会返回错误码和错误内容

        2. 当任务指明为`submit`时，必须明确给出参数`-alg`, `-proj`, `-m`

        3. `deploy`任务和`upload`任务有继承性关联，一般`upload`任务后紧跟`submit`，不应穿插其他任务。若多次`deploy`后才调用`subit`则会以最后一次`deploy`部署的节点和提交数据集开展训练。请勿多次调用`submit`，否则将提交多次相同的训练任务，造成不必要的开销

        4. 返回值-json格式字符串

           包含retcode，model_id, model_version, job_id等信息。系统需要保存model_id, model_version, job_id用于后续查询训练状态，绑定模型和开展预测服务。retcode为0表明任务执行成功，返回值格式如下：

           + 成功：`{'retcode': 0, 'model_id': 'xxx', 'model_version': 'xxx', 'jobid': 'xxx'}`

           + 失败：`{'retcode': 1}`

      + `query`:用于查询当前训练任务状态
        1. 返回值: 模型各个阶段的状态，多行字符串，每行为`success`, `failed`和`running`。`running`说明模型正在训练尚未结束，而若所有返回值全为`success`则模型训练成功完成否则若出现一次`failed`则模型训练以失败告终
        
        2. 当任务指明为`query`时，必须明确给出参数`-jid`
        
        3. 返回值-多行字符串
        
           每行字符串代表训练任务中个一个角色（arbiter，guest, host1, host2...)的工作状态，取值包括running，waiting，failed，success等
        
           判断训练是否正常完成的唯一方法是：多行字符串皆为success
        
           + 正常完成示例
        
             ```
             success
             success
             success
             success
             ```
        
           + 正常运行但为完成示例
        
             ```
             running
             running
             running 
             ```
        
           + 失败示例
        
             ```
             failed
             running
             ```
        
             ```
             failed
             failed
             ```
        
      + `load_bind`:必须在`submit`完成后才能执行，功能：加载与绑定，具有数据标签的一方绑定模型提供预测服务
        
        1. 当任务指明为`load_bind`时，必须明确给出参数`-mid`, `-mver`, `-mname`
        2. mname为模型名字，可自定义
        3. 返回值-单行字符串
           + 成功：`load_bind success.`
           + 失败：`load_bind failure.`
        
      + `predict`:必须在`load_bind`完成后才能执行，功能：完成模型预测 

        1. 当任务指明为`predict`时，必须明确给出参数`-mname`, `-params`

        2. 返回值-json格式字符串

           包含"prob","retmsg","retcode"等字段，"prob"为预测概率（预测结果）。只有个当retcode为0时表明预测任务正常执行，否则执行失败

           + 成功示例：`{"prob":0.30684422824464636,"retmsg":"success","retcode":0}`

           + 失败示例：

             `{"retmsg":"remote rpc exception","retcode":105}`

      + `delete`：删除之前的部署，需要给出与deploy时一样的参数

         1. 返回值-单行字符串
            + 成功：`delete success.`
            + 失败：`delete failure.`

4. 脚本功能总结示例

   + `deploy`

     ```
     python3 script.py -f deploy -pw 123456 123456 -id 1 2 -ip 1.1.1.1 2.2.2.2
     ```

   + `upload`:
     ```
     python3 script.py -f upload -gp 1 /root/data.csv -hp 1 /root/data1.csv 2 /root/data2.csv -proj example 
     ```
     
   + `submit`:

     ```
     python3 script.py -f submit -alg hetero_lr -proj example -m 1
     ```

   + `query`:

     ```
     python3 script.py -f query -jid jobid
     ```
     
   + `load_bind`:
     
     ```
     python3 script.py -f load_bind -mid model_id -mver model_version -mname toy_model
     ```
     
   + `predict`:
     
     ```
     python3 script.py -f predict -mname toy_model -params 1 2 3 4 0.5
     ```
     
   + `delete`：

       ```
       python3 script.py -f delete -pw 123456 123456 -id 1 2 -ip 1.1.1.1 2.2.2.2
       ```

5. 单主机实例:

    以下运行实例为在单个主机上部署kubeFate集群，并开展模型训练任务。

    ip为192.168.137.50的主机同时扮演host、guset的角色，训练数据breast_hetero_guest1.csv，breast_hetero_host1.csv事先存放于相应路径

    图示：

    ![workflow](.\pics\workflow.png)

    code:

    ```
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f deploy -ip 192.168.137.50 -id 1 -pw 123456 -u root
    deploy success.
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f upload -gp 1 /home/liyi/data/breast_hetero_guest1.csv -hp 1 /home/liyi/data/breast_hetero_host1.csv -proj test
    upload success.
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f submit -proj test -alg hetero_lr -m 1
    {'retcode': 0, 'model_id': 'arbiter-1#guest-1#host-1#model', 'model_version': '202102090702550067215', 'jobid': '202102090702550067215'}
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f query -jid 202102090702550067215
    running
    running
    running
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f query -jid 202102090702550067215
    success
    success
    success
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f load_bind -mid arbiter-1#guest-1#host-1#model -mver 202102090702550067215 -mname test
    load_bind success.
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f predict -mname test -params 1 2 3 4 5 6 7 8 9 10
    {"retmsg":"remote rpc exception","retcode":105}
    liyi@Ubuntu-Citi:~/docker-deploy$ python3 script.py -f delete -ip 192.168.137.50 -id 1 -pw 123456 -u root
    delete success.
    liyi@Ubuntu-Citi:~/docker-deploy$ 
    ```
    注意到，在执行predict任务时，返回结果中“retcode"不为0，即无法正常开展预测服务，可能原因是在单一主机上部署集群，host和guset共用同一服务器造成冲突。在多机集群部署时或可正常获取预测结果
    

