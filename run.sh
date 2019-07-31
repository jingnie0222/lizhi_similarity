#!/bin/bash
export LANG=zh_CN.UTF-8
curday=`date +%Y-%m-%d`


MYSQL=mysql #选用mysql程序
USER1=root   #设定用户名
PASSWORD1="lzxg@webqa" #设定数据库的用户密码
DB1=lizhimonitor #选定需要的数据库

#检查最近一个任务是否完成 
SQL_GET_TASKID="select task_id from lizhi_task order by task_id desc limit 1"
declare taskid=`$MYSQL -u${USER1} -p${PASSWORD1} -D ${DB1} -e "${SQL_GET_TASKID}" --skip-column-name`
echo $taskid

SQL_CHECK_TASK="select status from lizhi_task where task_id=$taskid"
declare status=`$MYSQL -u${USER1} -p${PASSWORD1} -D ${DB1} -e "${SQL_CHECK_TASK}" --skip-column-name`
echo $status

while true
do
    if [ $status -eq 2 ];then
        ps axu | grep chrome | grep "grep" -v | awk '{print $2}' | xargs kill 
        sleep 5
        # 先激活虚拟环境
        source ./venv/bin/activate
        python3 lizhi_similarity.py > test_log/log_$curday 2>&1 
        break
    else       
        sleep 300
        declare status=`$MYSQL -u${USER1} -p${PASSWORD1} -D ${DB1} -e "${SQL_CHECK_TASK}" --skip-column-name`
        echo $status
    fi
done
