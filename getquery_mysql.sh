#!/bin/bash
MYSQL=mysql #选用mysql程序

USER1=root   #设定用户名
PASSWORD1="lzxg@webqa" #设定数据库的用户密码
DB1=lizhimonitor #选定需要的数据库

USER2=main_project   #设定用户名
PASSWORD2="main_project" #设定数据库的用户密码
DB2=main_project #选定需要的数据库
HOST2="10.134.104.40"
 
#从召回率任务表中拉取最近一个任务 
SQL_GET_TASKID="select task_id from lizhi_task order by task_id desc limit 1"
declare new_taskid=`$MYSQL -u${USER1} -p${PASSWORD1} -D ${DB1} -e "${SQL_GET_TASKID}" --skip-column-name`
echo $new_taskid

start_time=`date +"\"%Y-%m-%d %H:%M:%S\""`
end_time=""
status="0"

#在精度监控任务表中创建任务
SQL_CREATE_NEWTASK="insert into lizhi_accu_mission (task_id, start_time, status) values ($new_taskid, $start_time, $status)"
$MYSQL -h${HOST2} -u${USER2} -p${PASSWORD2} -D ${DB2} -e "${SQL_CREATE_NEWTASK}" --skip-column-name

#获取任务中sogou和baidu都出立知的query 
SQL_GET_LIZHIQUERY="select query from lizhi_resultdetail where task_id=$new_taskid and sg_res_type=\"lizhi\" and bd_res_type=\"lizhi\" " #查找需要的数据sql语句
declare count=`$MYSQL -u${USER1} -p${PASSWORD1} -D ${DB1} -e "${SQL_GET_LIZHIQUERY}" --skip-column-name` #执行mysql的查询，并将其记录到count中
for list in $count                                                                                                      
    do
        echo "$list"
    done #读取得到的数据


#开始执行任务
SQL_START_TASK="update lizhi_accu_mission set status=1 where task_id=$new_taskid"
$MYSQL -h${HOST2} -u${USER2} -p${PASSWORD2} -D ${DB2} -e "${SQL_START_TASK}" --skip-column-name
