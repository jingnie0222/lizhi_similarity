#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# @author: zhaotj
# @time: 2019.4.23
# @file: run.py
# 
import requests
import datetime
import time
import os
from urllib.parse import quote

from segment import Segment


class quickRun(object):
    """docstring for run"""
    def __init__(self, query):
        self.query = query
        print("\nTask start.")

    def _run(self):
        query = self.query
        res = {}
        # sogou
        if os.path.exists("sogou"):
            os.remove("sogou")
        spliter = Segment()
        time.sleep(1)
        print(datetime.datetime.now())
        sogou_web = spliter.segment(url=("https://m.sogou.com/web/searchList.jsp?keyword=" + query), 
          output_folder="data/baidu", is_output_images=True, which_end="wap", site="sogou")
        print(datetime.datetime.now())

        # baidu
        if os.path.exists("baidu"):
            os.remove("baidu")
        spliter = Segment()
        time.sleep(1)
        print(datetime.datetime.now())
        baidu_web = spliter.segment(url=("https://m.baidu.com/s?wd=" + query), 
          output_folder="data/baidu", is_output_images=True, which_end="wap", site="baidu")
        print(datetime.datetime.now())

        # get localtime
        self.currentTime = time.strftime("%Y-%m-%d", time.localtime())
        self.__prepare4lizhi(self.currentTime)

        if sogou_web and baidu_web:
            text_a = sogou_web.text
            text_b = baidu_web.text
            line = {"realname": "kgm", "text_a": text_a, "text_b": text_b}
            headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-16LE"}
            base_resp = requests.post("http://xiangsidujiekou:8888/similarity-api", data=line, headers=headers)
            #if int(base_resp.text) == 0 and text_a and text_b:
            if base_resp.text and int(base_resp.text) == 0 and "None" not in text_a and "None" not in text_b:
                #print("Query:\t{}".format(query))
                #print("Sogou:\t{}".format(text_a))
                #print("Baidu:\t{}".format(text_b))
                #print("base_resp.text=%s" % base_resp.text)
                sogou_web.screenshot("image/" + self.currentTime + "/" + query + "_sogou.png")
                baidu_web.screenshot("image/" + self.currentTime + "/" + query + "_baidu.png")
                
                res['query'] = query
                res['sogou_text'] = text_a
                res['baidu_text'] = text_b
                res['sogou_pic'] = self.currentTime + "/" + quote(query) + "_sogou.png"
                res['baidu_pic'] = self.currentTime + "/" + quote(query) + "_baidu.png"
                
                return res
            else:   
                pass

    def _read(self):
        with open("sogou", "r", encoding="utf8") as sogou_fi, \
            open("baidu", "r", encoding="utf8") as baidu_fi:
                sogou_counter = 0
                baidu_counter = 0

                temp_sogou = [""]
                for i in sogou_fi.readlines():
                    if i == "\n":
                        continue

                    i = i.replace("\n", "")
                    if " - 搜狗搜索" in i:
                        if len(temp_sogou[sogou_counter]) > 0:
                            sogou_counter += 1
                            temp_sogou.append("")

                    else:
                        temp_sogou[sogou_counter] += (i + " ")

                temp_baidu = [""]
                for i in baidu_fi.readlines():
                    if i == "\n":
                        continue
                    
                    # i = i.replace("", "").replace("", "").replace("", "").replace("", "").replace("", "").replace("\n", "")
                    i = i.replace("\n", "")
                    if " - 百度" in i:
                        if len(temp_baidu[baidu_counter]) > 0:
                            baidu_counter += 1
                            temp_baidu.append("")

                    else:
                        temp_baidu[baidu_counter] += (i + " ")

                print(temp_sogou)
                print(temp_baidu)

                with open(os.path.join(os.getenv("GLUE_DIR"), "lizhi/test.tsv"), "wt", encoding="utf8") as fo:
                    length = len(temp_sogou)
                    counter = 0
                    label = 1

                    fo.write("Index\t#1 String\t#2 String\tlabel")

                    for i, j in zip(temp_baidu, temp_sogou):
                        # if counter == 800:
                            # break
                        with open("lizhiContext", "wt", encoding="utf8") as writer:
                            writer.write("Query:\t" + self.query + "\n")
                            writer.write("Sogou:\t" + j + "\n")
                            writer.write("Baidu:\t" + i + "\n")
                        if "None" in i or "None" in j:
                            continue
                        fo.write("\n")
                        fo.write("{}\t{}\t{}\t{}\n".format(counter, j, i, label))
                        counter += 1

    def __prepare4lizhi(self, currentTime):
        currentTime = currentTime
        if not os.path.exists(os.path.join("image", currentTime)):
            os.mkdir(os.path.join("image", currentTime))
        else:
            pass     
        


def main():
    spliter = Segment()

    if os.path.exists("baidu"):
        os.remove("baidu")
    with open("word", "r") as fi:
        for i in fi.readlines():
            spliter.segment(url=("https://m.baidu.com/s?wd=" + str(i)), output_folder="data/baidu", is_output_images=True, which_end="wap", site="baidu")
            time.sleep(1)

    if os.path.exists("sogou"):
        os.remove("sogou")
    with open("word", "r") as fi:
        for i in fi.readlines():
            spliter.segment(url=("https://m.sogou.com/web/searchList.jsp?keyword=" + str(i)), output_folder="data/baidu", is_output_images=True, which_end="wap", site="sogou")
            time.sleep(1)


if __name__ == "__main__":
    import sys
   
    quick_run = quickRun(sys.argv[1])

    quick_run._run()    

    # quick_run._read()  
