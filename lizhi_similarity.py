#!/usr/bin/python3
#-*-coding=utf8-*-

import pymysql
import run
import time
import DataFile
import Template
import Mail

query_file = "./lizhi_query"

query_db = pymysql.connect(host="host", user="root", passwd="passwd", db="lizhimonitor", charset="utf8")
query_corsur = query_db.cursor()

result_db = pymysql.connect(host="host", user="main_project", passwd="main_project", db="main_project", charset="utf8")
result_corsur = result_db.cursor()

report_tmp_path = "mail.html"

mail_to = ['yinjingjing@sogou-inc.com']

def get_taskid_query(query_file):   
    try:

        sql_get_taskid = "select task_id from lizhi_task order by task_id desc limit 1;"       
        query_corsur.execute(sql_get_taskid)
        task_id = query_corsur.fetchone()[0]
        print(task_id)
        sql_get_lizhiquery = "select query from lizhi_resultdetail where task_id=\"" \
                             + str(task_id) + "\"" \
                             + " and sg_res_type=\"lizhi\" and bd_res_type=\"lizhi\"; " 
        print(sql_get_lizhiquery)
        query_corsur.execute(sql_get_lizhiquery)
        result = query_corsur.fetchall()
        
        with open(query_file, 'w', encoding='utf8') as f_w:
            for element in result:
                write_str = element[0] + "\n"
                f_w.write(write_str)
        
        return task_id
                
    except Exception as err:
        print("[get_taskid_query]:%s" % err)
      

def create_new_task(task_id):
    try:
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        status = "0"        
        sql_create_task = "insert into lizhi_accu_mission (task_id, start_time, status) " \
                          + "values (\"%d\", \"%s\", \"%s\");" % (task_id, start_time, status)
        print(sql_create_task)
        result_corsur.execute(sql_create_task)
        result_db.commit()
    except Exception as err:
        print("[create_new_task]:%s" % err)
        
    
def run_task(task_id, query_file):
    #try:
    sql_check = "select status from lizhi_accu_mission where task_id=\"%d\";" % task_id
    print(sql_check)
    result_corsur.execute(sql_check)
    status_from_db = result_corsur.fetchone()[0]
    if status_from_db:
        status = "1"
        sql_run_task = "update lizhi_accu_mission set status = \"%s\" where task_id = \"%d\";" % (status, task_id)
        print(sql_run_task)
        result_corsur.execute(sql_run_task)
        result_db.commit()
        
        run_similarity(task_id, query_file)
    else:
        print("no task to run!")        
                
    #except Exception as err:
        #print("[run_task]:%s" % err)    

  

def run_similarity(task_id, query_file):
    
    with open(query_file, 'r', encoding='utf8') as f:
        for line in f.readlines():
            try:
                quick_run = run.quickRun(line.strip('\n'))
                res = quick_run._run()
                if res:
                    res['sogou_pic'] = "http://10.144.96.115/lizhi_similarity/" + res['sogou_pic']
                    res['baidu_pic'] =  "http://10.144.96.115/lizhi_similarity/" + res['baidu_pic']
                    #pymysql.escape_string 对内容中的" ' &等特殊字符进行转义，否则入库报错
                    sql_put_result = "insert into lizhi_accu_result (query, sogou_res, baidu_res, sogou_pic, baidu_pic, `precision`, status, task_id_id) "\
                                     + "values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%d\");" \
                                     % (pymysql.escape_string(res['query']), pymysql.escape_string(res['sogou_text']), pymysql.escape_string(res['baidu_text']), res['sogou_pic'], res['baidu_pic'], '0', '0', task_id)
                                     
                    print(sql_put_result)
                    result_corsur.execute(sql_put_result)
                    result_db.commit()
                    
            except Exception as err:
                print("[run_similarity]:%s" % err)
                continue
            

def finish_task(task_id):
    try:
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        status = "2"
        sql_finish_task = "update lizhi_accu_mission set status = \"%s\", end_time = \"%s\" where task_id = \"%d\";" % (status, end_time, task_id)
        print(sql_finish_task)
        result_corsur.execute(sql_finish_task)
        result_db.commit()
    except Exception as err:
        print("[finish_task]:%s" % err)
        
def send_mail(task_id):
    try:
        report_content = ""
        url = "http://fs.sogou/lizhi_accu_compare/mission_list/" + str(task_id) + "/"
        mail_title = Template.html_h3_title("立知结果精度对比运行完毕，请对结果进行标注:")
        mail_content = Template.html_p(url)
        
        report_content = mail_title + mail_content
        DataFile.write_full_file(report_tmp_path, report_content)
        Mail.sendMail("立知结果精度对比运行完毕，请对结果进行标注", report_tmp_path, mail_to)
    except Exception as err:
        print("[send_mail]:%s" % err)
    
    

if __name__ == "__main__":
    
    curr_task_id = get_taskid_query(query_file)
    create_new_task(curr_task_id)
    run_task(curr_task_id, query_file)
    finish_task(curr_task_id)
    send_mail(curr_task_id)
    
    
    
    
             
