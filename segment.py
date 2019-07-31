#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# @author: zhaotj
# @time: 2019.4.23
# @file: segment.py
# 
import os
import time
import bs4
import common
import requests
import shutil
import setting

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
from html.parser import HTMLParser
from PIL import Image
from urllib.parse import urljoin


class Segment:
    def __init__(self):
        # loading Options from webdriver
        options = Options()
        # options.binary_location = setting.CHROME_BINARY_LOCATION
        options.add_argument('--headless')
        options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1")
        # loading Chrome driver
        self.browser = webdriver.Chrome(chrome_options=options, executable_path=setting.DRIVER_PATH)
        # set the window size that you need
        #self.browser.set_window_size(setting.SCREEN_WIDTH, 400)
        self.browser.set_window_size(setting.SCREEN_WIDTH, 480)
        # loading HTML parser
        self.parser = HTMLParser()

    def segment(self, url, output_folder="output", is_output_images=False, which_end="wap", site="sogou"):
        self.url = url
        self.output_folder = self.remove_slash(output_folder)
        self.log = common.log()
        self.which_end = which_end
        self.site = site

        self.log.write("Crawl HTML Document from %s" % self.url)
        return self.__crawler()

        # self.log.write("Run Pruning on %s" % self.url)
        # self.__pruning()
        # self.log.write("Run Partial Tree Matching on %s" % self.url)
        # self.__partial_tree_matching()
        # self.log.write("Run Backtracking on %s" % self.url)
        # self.__backtracking()

        # self.log.write("Output Result JSON File on  %s" % self.url)
        # self.__output()

        # if is_output_images:
        #     self.log.write("Output Images on  %s" % self.url)
        #     self.__output_images()

        self.log.write("Finished on  %s" % self.url)

    def __crawler(self):
        self.browser.delete_all_cookies()
        self.browser.get(self.url)        
        self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        page_height = self.browser.find_element_by_tag_name("body").rect["height"]
        self.browser.set_window_size(setting.SCREEN_WIDTH, page_height)

        #common.prepare_clean_dir(self.output_folder)
        # self.browser.save_screenshot(self.output_folder + "/screenshot.png")
        
        return self.__get_lizhi_element()
        #self.currentTime = time.strftime("%Y-%m-%d", time.localtime())
        #self.__prepare4lizhi(self.currentTime)
       
        # with open(self.site, "at") as fo:
        #     if (self.site == "baidu"):
        #         # baidu
        #         print(self.browser.title)
        #         fo.write(self.browser.title + "\n")
        #         fo.write(str(self.__get_text_and_image("image/" + str(self.browser.title) + ".png")) + "\n")
        #         fo.write("\n")
        #     elif (self.site == "sogou"):
        #         # sogou
        #         print(self.browser.title)
        #         fo.write(self.browser.title + "\n")
        #         fo.write(str(self.__get_text_and_image("image/" + str(self.browser.title) + ".png")) + "\n")
        #         fo.write("\n")
        #     elif (self.site == "google"):
        #         # google
        #         pass
        #     elif (self.site == "bing"):
        #         # bing
        #         pass

    def __pruning(self):
        tagbody = self.soup.find("body")
        tagbody["lid"] = str(-1)
        tagbody["sn"] = str(1)
        self.allnodes = [tagbody]
        i = 0
        while len(self.allnodes) > i:
            children = []
            for child in self.allnodes[i].children:
                if isinstance(child, bs4.element.Tag):
                    children.append(child)
            sn = len(children)

            for child in children:
                child["lid"] = str(i)
                child["sn"] = str(sn)
                self.allnodes.append(child)
            i += 1
        pass

    def __partial_tree_matching(self):
        self.blocks = []

        lid_old = -2

        i = 0
        while i < len(self.allnodes):

            node = self.allnodes[i]

            if 'extracted' in node.attrs:
                i += 1
                continue
            sn, lid = int(node["sn"]), int(node["lid"])

            if lid != lid_old:
                max_window_size = int(sn / 2)
                lid_old = lid

            for ws in range(1, max_window_size + 1):

                pew, cew, new = [], [], []

                for wi in range(i - ws, i + 2 * ws):

                    if wi >= 0 and wi < len(self.allnodes) and int(self.allnodes[wi]["lid"]) == lid:
                        cnode = self.allnodes[wi]
                        if wi >= i - ws and wi < i:
                            pew.append(cnode)
                        if wi >= i and wi < i + ws:
                            cew.append(cnode)
                        if wi >= i + ws and wi < i + 2 * ws:
                            new.append(cnode)

                        pass

                isle = self.__compare_nodes(pew, cew)
                isre = self.__compare_nodes(cew, new)

                if isle or isre:
                    self.blocks.append(cew)
                    i += ws - 1
                    max_window_size = len(cew)
                    self.__mark_extracted(cew)
                    break
            i += 1
        pass

    def __mark_extracted(self, nodes):
        for node in nodes:
            node["extracted"] = ""
            lid = node["lid"]
            parent = node
            while parent.parent is not None:
                parent = parent.parent
                parent["extracted"] = ""
                parent["sid"] = lid

            nodecols = [node]
            for nodecol in nodecols:
                for child in nodecol.children:
                    if isinstance(child, bs4.element.Tag):
                        nodecols.append(child)
                nodecol["extracted"] = ""

    def __compare_nodes(self, nodes1, nodes2):
        if len(nodes1) == 0 or len(nodes2) == 0:
            return False

        return self.__get_nodes_children_structure(nodes1) == self.__get_nodes_children_structure(nodes2)
        pass

    def __get_nodes_children_structure(self, nodes):
        structure = ""
        for node in nodes:
            structure += self.__get_node_children_structure(node)
        return structure

    def __get_node_children_structure(self, node):
        nodes = [node]
        structure = ""
        for node in nodes:
            for child in node.children:
                if isinstance(child, bs4.element.Tag):
                    nodes.append(child)
            structure += node.name
        return structure

    def __backtracking(self):

        for node in self.allnodes:
            if (node.name != "body") and (node.parent is not None) and ('extracted' not in node.attrs) and (
                    'extracted' in node.parent.attrs):
                self.blocks.append([node])
                self.__mark_extracted([node])
        pass

    def __get_element(self, node):
        # for XPATH we have to count only for nodes with same type!
        length = 1
        for previous_node in list(node.previous_siblings):
            if isinstance(previous_node, bs4.element.Tag):
                length += 1
        if length > 1:
            return '%s:nth-child(%s)' % (node.name, length)
        else:
            return node.name

    def __get_css_selector(self, node):
        path = [self.__get_element(node)]
        for parent in node.parents:
            if parent.name == "[document]":
                break
            path.insert(0, self.__get_element(parent))
        return ' > '.join(path)

    def __get_css_background_image_urls(self, node):
        nodes = [node]
        image_urls = []
        structure = ""
        for node in nodes:
            for child in node.children:
                if isinstance(child, bs4.element.Tag):
                    nodes.append(child)
        for node in nodes:
            try:
                css_selector = self.__get_css_selector(node)
                url = self.browser.find_element_by_css_selector(css_selector).value_of_css_property("background-image")
                if url != "none":
                    url = url.replace('url(', '').replace(')', '').replace('\'', '').replace('\"', '')
                    url = urljoin(self.url, url)
                    image_urls.append(url)
            except:
                pass
        return image_urls

    def __get_css_selector(self, node):
        path = [self.__get_element(node)]
        for parent in node.parents:
            if parent.name == "[document]":
                break
            path.insert(0, self.__get_element(parent))
        return ' > '.join(path)

    def __rgba2RGBA(self, rgba):
        try:
            rgba = rgba.replace("rgba(", "").replace(")", "")
            (R, G, B, A) = tuple(rgba.split(","))
            return int(R), int(G), int(B), float(A)
        except:
            return 0, 0, 0, 0

    def __get_css_background_color(self, node):
        nodes = [node]
        for p in node.parents:
            nodes.append(p)

        (R, G, B) = (255, 255, 255)
        for node in nodes:
            try:
                css_selector = self.__get_css_selector(node)
                color = self.browser.find_element_by_css_selector(css_selector).value_of_css_property(
                    "background-color")

                Rn, Gn, Bn, A = self.__rgba2RGBA(color)

                if A == 1:
                    (R, G, B) = (Rn, Gn, Bn)
                    break
            except:
                pass
        return R, G, B

    def __get_location_by_css(self, css_selector):
        return self.browser.find_element_by_css_selector(css_selector).location

    def __get_size(self, css_selector):
        return self.browser.find_element_by_css_selector(css_selector).size

    def __get_text_and_image(self, image_path):
        MIN_TEXT_LENGTH = 5

        if self.site == "baidu":
            class_name = "c-result"
            # try:
            #     temp = self.browser.find_elements_by_class_name(class_name)
            #     temp[0].screenshot(image_path)
            #     return temp[0].text
            # except:
            #     return None

            # 百度立知：图谱，精选摘要，优质问答，百度百科，百度官网
            tagger = ["ks_general", "person_couple", "wise_word_poem", 
            "kg_answer_poem", "sg_answer_poem", "kg_law", "kg_qanda", 
            "wenda_abstract", "bk_polysemy", "sg_kg_entity", "www_sitelink_normal"]

            for i in tagger:
                # temp = self.browser.find_elements_by_xpath('//div[contains(@tpl, {})]'.format(i))
                temp = self.browser.find_elements_by_css_selector('[tpl="{}"]'.format(i))
                if len(temp) > 0 and len(temp[0].text) >= MIN_TEXT_LENGTH:
                    temp[0].screenshot(image_path) 
                    return temp[0].text
                else:
                    pass

            return None

        elif self.site == "sogou":
            class_name = "vrResult"
            temp = self.browser.find_elements_by_class_name(class_name)
            num = len(temp)

            for i in range(num):
                if (len(temp[i].text) < MIN_TEXT_LENGTH):
                    continue
                else:
                    try:
                        temp[i].find_element_by_class_name("icon-known")
                        temp[i].screenshot(image_path)
                        return temp[i].text
                    except:
                        if ("50026601" in temp[i].get_attribute("id") or
                            "50026401" in temp[i].get_attribute("id") or
                            "50026301" in temp[i].get_attribute("id") or
                            "kmap-jzvr-81-container'" in temp[i].get_attribute("id")):
                            temp[i].screenshot(image_path)
                            return temp[i].text

            return None
        elif self.site == "bing":
            class_name = ""
        elif self.site == "google":
            class_name = ""
        else:
            sys.exit("site not found")

    def __get_lizhi_element(self):
        MIN_TEXT_LENGTH = 5

        if self.site == "baidu":
            class_name = "c-result"

            # 百度立知：图谱，精选摘要，优质问答，百度百科，百度官网
            tagger = ["ks_general", "person_couple", "wise_word_poem", 
            "kg_answer_poem", "sg_answer_poem", "kg_law", "kg_qanda", 
            "wenda_abstract", "bk_polysemy", "sg_kg_entity", "www_sitelink_normal"]

            for i in tagger:
                # temp = self.browser.find_elements_by_xpath('//div[contains(@tpl, {})]'.format(i))
                temp = self.browser.find_elements_by_css_selector('[tpl="{}"]'.format(i))
                if len(temp) > 0 and len(temp[0].text) >= MIN_TEXT_LENGTH:
                    return temp[0]
                else:
                    pass

            return None

        elif self.site == "sogou":
            class_name = "vrResult"
            temp = self.browser.find_elements_by_class_name(class_name)
            num = len(temp)

            for i in range(num):
                if (len(temp[i].text) < MIN_TEXT_LENGTH):
                    continue
                else:
                    try:
                        temp[i].find_element_by_class_name("icon-known")
                        return temp[i]
                    except:
                        if ("50026601" in temp[i].get_attribute("id") or
                            "50026401" in temp[i].get_attribute("id") or
                            "50026301" in temp[i].get_attribute("id") or
                            "kmap-jzvr-81-container'" in temp[i].get_attribute("id")):
                            return temp[i]

            return None
        elif self.site == "bing":
            class_name = ""
        elif self.site == "google":
            class_name = ""
        else:
            sys.exit("site not found")


    def __output(self):

        segids = []
        rid = 0

        segs = dict()
        for i, block in enumerate(self.blocks):
            # texts
            texts, images, links, cssselectors, location, size = [], [], [], [], [], []

            for node in block:
                # extract text from node
                for text in node.stripped_strings:
                    texts.append(text)
                # extract text from node -- end

                # extract images in css background
                background_image_urls = self.__get_css_background_image_urls(node)
                for url in background_image_urls:
                    dict_img = dict()
                    dict_img["alt"] = ""
                    dict_img["src"] = urljoin(self.url, url)
                    r, g, b = self.__get_css_background_color(node)
                    dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                    images.append(dict_img)
                # extract images in css background -- end

                # extract images in <img> element
                for img in node.find_all("img"):
                    dict_img = dict()
                    if "src" in img.attrs:
                        dict_img["src"] = urljoin(self.url, img["src"])
                    if "alt" in img.attrs:
                        dict_img["alt"] = img["alt"]
                    images.append(dict_img)
                    r, g, b = self.__get_css_background_color(img)
                    dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                # extract images in <img> element

                # extract hyperlink from node
                for link in node.find_all("a"):
                    if "href" in link.attrs:
                        links.append({"href": urljoin(self.url, link["href"])})
                # extract hyperlink from node -- end

                cssselectors.append(self.__get_css_selector(node))
                location.append(self.__get_location_by_css(self.__get_css_selector(node)))
                size.append(self.__get_size(self.__get_css_selector(node)))

                # if self.which_end == "wap":
                #     if (self.__get_css_selector(node) == 
                #     "html > body:nth-child(2) > div:nth-child(5) > div:nth-child(4) > div:nth-child(2) > div > div > div:nth-child(4) > div:nth-child(2) > a > p"
                #     or 
                #     self.__get_css_selector(node) == 
                #     "html > body:nth-child(2) > div:nth-child(5) > div:nth-child(4) > div:nth-child(2) > div > div > div:nth-child(4) > div:nth-child(2) > a > p:nth-child(2)"):
                #         for text in node.stripped_strings:
                #             print(text)

                #     if (self.__get_css_selector(node) == 
                #     "html > body:nth-child(2) > div:nth-child(5) > div:nth-child(4) > div:nth-child(2) > div > div > a:nth-child(5)"
                #     or
                #     self.__get_css_selector(node) == 
                #     "html > body:nth-child(2) > div:nth-child(3) > div:nth-child(4) > div:nth-child(2) > div > div > a:nth-child(5)"):

                #         # for parent in node.parents:
                #         #     print(self.__get_location_by_css(self.__get_css_selector(parent)))
                #         # aaa = self.__get_location_by_css(self.__get_css_selector(node))
                #         # bbb = self.__get_size(self.__get_css_selector(node))
                #         # self.browser.find_element_by_css_selector(self.__get_css_selector(node)).screenshot(self.output_folder + "/hhh.png")
                #         for text in node.stripped_strings:
                #             print(text)
                        

                # if self.which_end == "web":
                #     if (self.__get_css_selector(node) == 
                #         "html > body:nth-child(2) > div > div:nth-child(6) > div:nth-child(4) > div:nth-child(6) > div > div:nth-child(2)"
                #         or 
                #         self.__get_css_selector(node) == 
                #         "html > body:nth-child(2) > div > div:nth-child(8) > div:nth-child(4) > div:nth-child(7) > div > div:nth-child(2)"):
                #         for text in node.stripped_strings:
                #             print(text)


            if len(texts) == 0 and len(images) == 0:
                continue

            lid = block[0]["lid"]

            if lid not in segids:
                segids.append(lid)
            sid = str(segids.index(lid))

            if sid not in segs:
                segs[sid] = {"segment_id": int(sid), "css_selector": self.__get_css_selector(block[0].parent), "records": []}

            segs[sid]["records"].append(
                {"record_id": rid, "texts": texts, "images": images, "css_selector": cssselectors, "links": links, "location": location, "size": size})
            rid += 1

        self.json_data = dict()
        self.json_data["segments"] = [value for key, value in segs.items()]
        self.json_data["url"] = self.url
        self.json_data["title"] = self.browser.title

        

        # region = (int(aaa['x']), int(aaa['y']), int(aaa['x'] + bbb['width']), int(aaa['y'] + bbb['height']))
        # i = Image.open(self.output_folder + "/screenshot.png")
        # i.crop(region).save(self.output_folder + "/hhh.png")

        common.save_json(self.output_folder + "/result.json", self.json_data, encoding=setting.OUTPUT_JSON_ENCODING)

    def __output_images(self):
        tmp_path = self.output_folder + "/tmp"
        path = self.output_folder + "/images"
        common.prepare_clean_dir(tmp_path)
        common.prepare_clean_dir(path)
        for segment in self.json_data["segments"]:
            for record in segment["records"]:
                for i, image in enumerate(record["images"]):
                    try:
                        file_name = "%s_%s" % (record["record_id"], i)
                        source_file_name_only = tmp_path + "/" + file_name
                        original_extension = image["src"].split('/')[-1].split('.')[-1].split("?")[0]
                        source_file_name = source_file_name_only + "." + original_extension
                        target_file_name = path + "/" + file_name + "." + setting.OUTPUT_IMAGE_TYPE

                        r = requests.get(image["src"], stream=True, headers={'User-agent': 'Mozilla/5.0'})
                        if r.status_code == 200:
                            with open(source_file_name, 'wb') as f:
                                r.raw.decode_content = True
                                shutil.copyfileobj(r.raw, f)
                        else:
                            continue

                        [R, G, B] = [int(a) for a in image["bg_color"].split(",")]
                        im = Image.open(source_file_name).convert('RGBA')
                        bg = Image.new("RGB", im.size, (R, G, B))
                        bg.paste(im, im)
                        im = bg
                        im.save(target_file_name)

                        image["path"] = target_file_name
                    except Exception:
                        pass

        common.save_json(self.output_folder + "/result.json", self.json_data, encoding=setting.OUTPUT_JSON_ENCODING)

        shutil.rmtree(tmp_path)

    def __prepare4lizhi(self, currentTime):
        currentTime = currentTime
        if not os.path.exists(os.path.join("image", currentTime)):
            os.mkdir(os.path.join("image", currentTime))
        else:
            pass

    def remove_slash(self, path):
        for i in range(len(path)):
            if path.endswith('/'):
                path = path[:-1]
            if path.endswith('\\'):
                path = path[:-1]
        return path
