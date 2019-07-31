# -*- coding: utf-8 -*-
#import mysql.connector
import socket
#from lib import AceConfLoader
import configparser
import codecs
import pymysql
   
#support from read from mysql setting file.
def init_db(mysql_conf_path, sector = "Mysql"):
    #mysql_base_config = AceConfLoader.AceConfLoader(mysql_conf_path)
    #mysql_config = mysql_base_config.loadconfBySector(sector)
    cf = configparser.ConfigParser()
    cf.readfp(codecs.open(mysql_conf_path, "r", "utf8")) #注意需要用encoding处理中文的输出问题
    mysql_config = cf[sector]
    print(mysql_config)
    db = DBHelper({ "host":mysql_config['host'], 
                    "port":int(mysql_config['port']),
                    "user": mysql_config['username'],
                    "passwd": mysql_config['password'],
                    "dbname":mysql_config['dbname'],
                    "charset": mysql_config['charset']})
    print ("Init DB for: " + mysql_config['dbname'], 0)
    return db
   
class DBHelper:
    error_code = ''
    error_msg = ""
    _conn = None
    _cur = None
    _conf = None

    # 初始化参数
    def __init__(self, config):
        self._conf = config
        self._get_conn(config)

    # 获取数据库连接
    def _get_conn(self, config):
        #somehow needit to using no password.
        if(not 'passwd' in config.keys()):
            print ("using no passwd mode.",2)
            try:
                self._conn = pymysql.connect(host=config['host'],
                                                     port=config['port'],
                                                     user=config['user'],
                                                     db=config['dbname'],
                                                     charset=config['charset'])
            except Exception as e:
                self.error_code = e.args[0]
                self.error_msg = e.args[1]
                self._print_error()
        else:
            try:
                self._conn = pymysql.connect(host=config['host'],
                                                     port=config['port'],
                                                     user=config['user'],
                                                     passwd=config['passwd'],
                                                     db=config['dbname'],
                                                     charset=config['charset'])
            except Exception as e:
                self.error_code = e.args[0]
                self.error_msg = e.args[1]
                self._print_error()
        self._cur = self._conn.cursor()

    #打印异常
    def _print_error(self):
        if self.error_code == 1045:
            print ( "can not connect to the database, user name or password error")
        elif self.error_code == 1049:
            print ( "database does not exist.")
        elif self.error_code == 1146:
            print ( "query fails, the data table does not exist.")
        elif self.error_code == 1054:
            print ( "The operation failed, the field does not exist")
        elif self.error_code in (1158, 1159, 1160, 1161):
            print ( "network error occurs, read / write errors, check the network connection status")
        elif self.error_code == 2003:
            print ( "database connection fails, check the host or port configuration")
        else:
            print("Error Code: %s,Error Message: %s" % (self.error_code,
                                                        self.error_msg))

    # 关闭连接
    def close(self):
        if self._cur is not None:
            self._cur.close()
        if self._conn is not None:
            self._conn.close()

    # 建立数据表usertable
    def create(self, sql):
        self._execute(sql)

    # 查询表信息
    # bycolumnname为True的时候，直接返回由dict组成的数组，符合类似PHP的设计思路
    def query(self, sql, bycolumnname = True):
        results = None
        try:
            self._cur.execute(sql)
            results = self._cur.fetchall()
            if(bycolumnname):
                columns = self._cur.description
                #把推导式改回普通方式
                return_list = []
                for value in results:
                    single_row = {columns[index][0]:column for index, column in enumerate(value)}
                    single_row = self._fix_row(single_row) #把弱智的单行varchar数据修一下
                    return_list.append(single_row)
                #return [{columns[index][0]:column for index, column in enumerate(value)} for value in results]
                return return_list
        except Exception as e:
            self.error_code = e.args[0]
            self.error_msg = e.args[1]
            self._print_error()
        return results

    # 插入数据
    def insert(self, tablename, data):
        key_str = r'`'
        val_str = '\''
        for (k, v) in data.items():
            v = str(v) #adjust for non-str input
            v = v.replace("'", "\"")
            key_str += (k + r'`,`')
            val_str += (v + "','")
        key_str = key_str[:-2]
        val_str = val_str[:-2]
        sql = r'INSERT INTO %s (%s) VALUES (%s);' % (tablename, key_str, val_str)
        return self._execute(sql)

    # 执行语句
    def _execute(self, sql):
        try:
            result = self._cur.execute(sql)
            self._conn.commit()
            return result
        except Exception as e:
            self.error_code = e.args[0]
            self.error_msg = e.args[1]
            self._print_error()
        return False

    # 删除数据
    def delete(self, tablename, condition):
        sql = 'DELETE FROM %s WHERE %s' % (tablename, condition)
        self._execute(sql)
        
    #选取指定sql的某个列全部数据作为list返回
    def fetch_one_column(self, sql, columnname):
        data_tmp = self.query(sql, bycolumnname = True)
        return_list = []
        for line in data_tmp:
            return_list.append(line.get(columnname, ""))
        return return_list

    def fetch_first(self, sql, bycolumnname = True, fix_column = False):
        rs = self.query(sql, bycolumnname)
        if(not rs):
            return None
        if(len(rs) <= 0):
            return None
        else:
            if(fix_column):
                return self._fix_row(rs[0])
            else:
                return rs[0]
            
    #对一条结果进行encoding
    def _fix_row(self, result_row):
        for k,v in result_row.items():
            if(isinstance(v, bytearray) or isinstance(v, bytes)):
                result_row[k] = v.decode(self._conf["charset"])
        return result_row

    #获取第一条结果的指定栏内容
    def result_first(self, table_name, columnname, condition = ''):
        sql = 'SELECT ' + columnname + ' FROM ' + table_name 
        if(len(condition) > 0):
            sql = sql + " WHERE " + condition
        rs = self.query(sql, bycolumnname = True)
        if(not rs):
            return None
        if(len(rs) <= 0):
            return None
        else:
            if(columnname in rs[0]):
                return rs[0][columnname]
            else:
                return None
        
    #update_table的别名
    def update(self, tablename, data, condition):
        exec_result = self.update_table(tablename, data, condition)
        return exec_result
        
    # 更新数据
    # 把执行结果返回，方便捕捉执行失败的False
    def update_table(self, tablename, data, condition):
        update_str = r'`'
        for (k, v) in data.items():
            v = str(v)
            v = v.replace("'", '&#039;')
            update_str += (k + r"`='" + v + r"',`")
        update_str = update_str[:-2]
        sql = 'UPDATE %s SET %s WHERE %s' % (tablename, update_str, condition)
        exec_result = self._execute(sql)
        return exec_result
        
    def add_value(self, tablename, colname, value, condition):
        sql = 'UPDATE %s SET %s=%s+%s WHERE %s' % (tablename, colname, colname, value, condition)
        exec_result = self._execute(sql)
        return exec_result

    # 批量更新数据
    def dbatch_update(self, tablename, data_list):
        for data, cond in data_list:
            self.update_table(tablename, data, cond)

    # 删除数据表
    def drop(self, tablename):
        sql = 'drop table %s' % (tablename)
        self._execute(sql)
        
    #get last insert_id for review
    def insert_id(self):
        return self._cur.lastrowid
    
    #get pk. in case of delete by pk
    def get_primary_key(self, tablename):
        sql = 'SELECT COLUMN_KEY,COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name=\'' + tablename + '\' AND COLUMN_KEY=\'PRI\'';
        rs = self.query(sql, True)
        return rs[0]["COLUMN_NAME"]
        
    def show_conn_info(self):
        print("Connection Info:", self._conf.items())

    def show_db_info(self):
        sql = r'show databases;'
        ret = self._cur.execute(sql)
        for row in self._cur.fetchall():
            print(row)

    def show_table_info(self):
        sql = r'show tables;'
        ret = self._cur.execute(sql)
        for row in self._cur.fetchall():
            print(row)
            
    #以当前host为key获取锁，用于task型测试
    #成功返回True，失败返回False
    #如果不存在当前ip的话则自动添加锁
    def get_lock(self, table_name, key = 'lock_host', columnname = 'lock_status'):
        rs = self.result_first(table_name, columnname, key + "='" + self._get_ip() + "'")
        if(rs == None):
            self.insert(table_name, {'lock_host' : self._get_ip(), 'lock_status' : 1})
            return True
        elif(rs == 0):
            self.update_table(table_name, {'lock_status':1}, key + "='" + self._get_ip() + "'")
            #自动添加锁
            return True
        else:
            #如果当前上锁则返回False，告诉调用者等待下一次轮询
            return False
        
    def release_lock(self, table_name, key = 'lock_host', columnname = 'lock_status'):
        rs = self.result_first(table_name, columnname, key + "='" + self._get_ip() + "'")
        if(rs == None):
            self.insert(table_name, {'lock_host' : self._get_ip(), 'lock_status' : 0})
        else:
            self.update_table(table_name, {'lock_status':0}, key + "='" + self._get_ip() + "'")
        return True

    def _get_ip(self):
        return socket.gethostbyname(socket.gethostname())
        
if __name__ == '__main__':
    test()

