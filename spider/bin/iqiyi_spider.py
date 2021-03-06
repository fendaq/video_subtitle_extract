#!/usr/bin/env python3
#coding=utf-8

import json
import re
import time
import codecs
import threading
import os
import multiprocessing
import Queue
import sys
import urllib2
import traceback

from bs4 import BeautifulSoup

import htmlutil

#多线程的锁
mutex = threading.Lock()


class IqiyiSpider(object):
  def __init__(self):
    self.seed_url = "http://www.iqiyi.com/zongyi/"
    self.pattern_url = "iqiyi.com/"
    self.link_set = set()
    self.link_queue = Queue.Queue()
    
    #self.link_queue = multiprocessing.Queue()

    self.link_file='../link/linkbase'
    self.crawed_link_file='../link/crawed_link'
    self.output_file = '../output/iqiyi.txt'
    self.filter_file = '../config/iqiyi.filter.url'


    self.crawed_link_list = set()
    self.process_num = 1

    self.result_fw = codecs.open(self.output_file, 'a','utf-8')

    
    self.filter_url_list = []
    with codecs.open(self.filter_file, 'r', 'utf-8') as filter_fr:
      for line in filter_fr:
        if len(line.strip()) != 0:
          self.filter_url_list.append(line.strip())

  def __del__(self):
    print("exiting...")
    self.save_link()

    self.result_fw.close()


  def is_filter_url(self, url):
    '''判断是否应该是被过滤掉的url'''
    for line in self.filter_url_list:
      if url.decode("utf-8").find(line) != -1:
        return True
    return False


  def get_html(self,url):
    html = ""
    #url = url.split()[0]
    
    try:
      website = urllib2.urlopen(url,timeout=5)
      html = website.read()
    #  html = html.decode('gbk')
    except:
      traceback.print_exc()
      print("net except: ", url)
      return ""

    return html


  def save_link(self):
    ''' 保存link到文件'''
    # 保存队列里的link
    
    link_filewrite = codecs.open(self.link_file, 'w', 'utf-8')
    while not self.link_queue.empty():
      link = self.link_queue.get()
      try:
        link_filewrite.write(link+'\n')
      except:
        print("save error link: %s" % link)
        pass
    link_filewrite.close()
    print("save link in queue ok.")

    # 保存已经抓取的link
    fw = codecs.open(self.crawed_link_file, 'w', 'utf-8')
    for link in self.crawed_link_list:
      try:
        fw.write(link.decode('utf-8')+'\n')
      except:
        print("save error crawled link: %s" % link)
    fw.close()

    print("save crawled link ok.")
  

  def load_link(self):
    ''' load link到内存'''
    if os.path.exists(self.crawed_link_file):
      fr = codecs.open(self.crawed_link_file, 'r','utf-8')
      for line in fr:
        line = line.strip()
        self.crawed_link_list.add(line)
      fr.close()

    if os.path.exists(self.link_file):
      fr = codecs.open(self.link_file, 'r', 'utf-8')
      for line in fr:
        line = line.strip()
        if line not in self.crawed_link_list:
          self.link_queue.put(line)
          self.link_set.add(line)
      fr.close() 

    if self.link_queue.empty():
      self.link_queue.put(self.seed_url)
      self.link_set.add(self.seed_url)
    print("load link success")

  def craw(self):
    step = 0
    while step < 20000:
      if step % 1000 == 0:
        print("---------process %d url" % step)

      url = self.link_queue.get()
      if url in self.crawed_link_list and url != self.seed_url:
        continue

      print(url)
      html = self.get_html(url)
      if html == "":
        continue
      html = str(html)

      self.crawed_link_list.add(url)

      # 提取正文内容
      class_info,video_title = self.get_class(html)
      if class_info =="":
        pass
      else:
        self.result_fw.write(class_info.decode("utf-8") + '\t'  + video_title.decode("utf-8") + '\t' +  url + '\n')

      all_links = htmlutil.get_all_links(html)
      for link in all_links:
        link = link.split('#')[0]
        link = link.split('?')[0]
        if not self.is_special_pattern_url(link):
          continue
  
        if link not in self.crawed_link_list and link not in self.link_set:
          if self.is_filter_url(link) == False:
            self.link_queue.put(link)
            self.link_set.add(link)
      step += 1

  def is_special_pattern_url(self,url):
    if url.find(self.pattern_url) == -1 :
      return False
    return True

  def get_class(self,html):
    ''' 通过html， 获取视频的分类和标题'''
    soup=BeautifulSoup(html,'lxml')
    class_html=soup.findAll('span',{'id':"datainfo-navlist"})
    if len(class_html) == 0:
      class_html=soup.findAll('span',{'id':"widget-videonav"})
      if len(class_html) == 0:
        return "",""

    s = '<html><body>'+str(class_html[0])+'</body></html>'
    soup2 = BeautifulSoup(s,'lxml')
    alist=[]
    for i in soup2.find_all('a'):
      i = htmlutil.remove_html_tag(str(i).strip())
      alist.append(i.strip())
    navi_text = "_".join(alist)

    video_title = soup.findAll('span', {'id':"widget-videotitle"})
    if len(video_title) == 0:
      video_title = soup.findAll('h1', {'id':"widget-videotitle"})
    video_title = htmlutil.remove_html_tag(str(video_title[0]).strip())
    video_title = "".join(video_title.split())
    video_title = "".join(video_title.split('：'))
    return navi_text, video_title



  def start(self):
    ''' 开始爬取网页的内容'''
    self.load_link()
    self.craw()
    

if __name__ == '__main__':
  spider = IqiyiSpider()
  spider.start()


