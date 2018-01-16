#encoding:utf-8

import json
import zlib
import datetime
import urllib
import urllib.request
import urllib.parse
import re
import os
import socket

from PIL import Image
from bs4 import BeautifulSoup


class Spider():

    def __init__(self):
        self.__dir_stack = []
        self.__file_name = ''
        self.__scenefile_name = ''  # 断点续传绝对文件路径和名
        self.__doneset = {}         # 不重复扫描
        self.__done_num = 0         # 要在外部文件中记录的已经访问完毕的前多少个文件
        self.__done_tmp = 0         # 此次运行spider程序到关闭或者退出之前又完成了多少个元素的访问
        self.__last_element = []    # 记录没有被访问过的元素

    def getScene(self):
        return self.__scenefile_name

    def convertJif2Png(self, infile):

        infile_t = '%s%s' % (self.getworkdir(), infile)
        outfile = '%s%s.jpg' % (self.getworkdir(), infile[:-4])
        Image.open('%s%s' % (self.getworkdir(), infile)).convert('RGB').save(outfile)
        os.remove(infile_t)
        return '%s.jpg' % infile[:-4]

    def setScene(self,name):
        '''如果不设置 则可以用自己的方法迭代。'''

        self.__scenefile_name = self.getworkdir() + name
        f = ''
        try:
            f = open(self.__scenefile_name, 'r+')
            self.__done_num = (int)(f.read())
        except:
            f = open(self.__scenefile_name, 'w+')
            f.write('0')
            self.__done_num = 0
        f.close()

    def initLoop(self):
        '''把已经扫描过的文件跳过 必须保证当前__file_name的值是
        要扫描内容的完整路径和文件名。
        return: 返回总数和已经完成的总个数'''

        f = open(self.__file_name,'r+')
        cot = 1
        self.__done_tmp = 0
        while True:
            line = f.readline()
            if not line:
                break
            line = line[:-1]
            if cot <= self.__done_num: # 如果访问过
                self.__doneset[line] = 1
            else:
                self.__last_element.append(line)
            cot+=1
        f.close()
        return len(self.__last_element) + self.__done_num , self.__done_num

    def getNext(self):
        '''得到没有被迭代的下一个元素。
        如果已经完成所有没有被访问过的元素 则返回None。
        '''

        while self.__done_tmp < len(self.__last_element):
            if self.__last_element[self.__done_tmp] in self.__doneset:
                self.__done_tmp+=1
            else:
                f = open(self.__scenefile_name, 'w+')
                f.write((str)(self.__done_num + self.__done_tmp))
                print(self.__done_num + self.__done_tmp)
                f.close()
                self.__doneset[self.__last_element[self.__done_tmp]] = 1
                return self.__last_element[self.__done_tmp]
            f = open(self.__scenefile_name, 'w+')
            f.write((str)(len(self.__last_element) + self.__done_num))
            f.close()
        return None

    def setfilename(self,name):
        self.__file_name = self.getworkdir() + name

    def getworkdir(self):
        if len(self.__dir_stack) <= 0:
            return None
        else:
            return self.__dir_stack[len(self.__dir_stack)-1]

    def removeworkdir(self):
        if len(self.__dir_stack) <= 0:
            return None
        else:
            return self.__dir_stack.pop()

    def setworkdir(self,sdir):  #设置工作目录
        self.__dir_stack.append(sdir)
        try:
            os.mkdir(sdir)
        except:
            pass

    def dictoJson(self,dic):
        return json.dumps(dic, sort_keys=True, ensure_ascii=False, indent=2)

    def savefile(self,info,tp='w+'):
        f = open(self.__file_name,tp)
        f.write(info)
        f.close()

    def getResponse(self,url,data=None,times=3):#有data域表明是一个post提交
        if data != None:
            data = urllib.parse.urlencode(data)
        response = None
        errorText = ''
        now = datetime.datetime.now()
        now = now.strftime('%c')
        errorText = now + '\n'
        errorText = 'happen on ' + url + ':\n'
        html = ''
        try:
            req_header = {'user_agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)','Accept-encoding':'*'}
            req = urllib.request.Request(url,None,req_header)

            '''
            设置代码，等被屏蔽的时候用得
            proxy = urllib.request.ProxyHandler({'http': '133.130.111.99:18000'})
            opener = urllib.request.build_opener(proxy)
            urllib.request.install_opener(opener)
            '''

            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
            # 5秒放弃图片
            response = opener.open(req, data, timeout=5)
            gzipped = response.headers.get('Content-Encoding')
            html = response.read()
            if gzipped:
                 html = zlib.decompress(html, 16+zlib.MAX_WBITS)
            return html
        except urllib.request.URLError as e:
              errorText = "urllib.request.URLError\n"
              if hasattr(e,'code'):
                  try:
                      errorText = errorText + 'e.code:' + (str)(e.code) + '\n'
                  except:
                      errorText = errorText + 'e.code:unknow\n'
              if hasattr(e,'reason'):
                  try:
                      errorText = errorText + 'e.reason:' + (str)(e.reason) + '\n'
                  except:
                      errorText = errorText + 'e.reason:unknow' + '\n'
        except socket.timeout as e:
              errorText = errorText + 'request timeout' + '\n'
              if times <= 1:
                  return "-3"
              return self.getResponse(url,times=times-1)
        return html

    def getSoup(self, url, data=None, response=None, uncode='utf-8', untype='html5lib'):
        '''untype为解码器类型 默认为html5lib 还有lxml 和 html.parser。'''

        if response is None:
             response = self.getResponse(url,data)

        if response is not None:
             return BeautifulSoup(response, untype, from_encoding=uncode)

        return None

    def getTags(self, ssoup, tag, extra=None):
        if isinstance(tag, list): #如果是findAll
            if extra == None:
                return ssoup.findAll(tag)
            else:
                return ssoup.findAll(tag,extra)
        else:                          #如果是search
            if extra == None:
                return ssoup.find(tag)
            else:
                return ssoup.find(tag,extra)

    def Reg(self,reg,text):
        re1 = re.compile(reg)
        match = re1.search(text)
        if match == None:
            return 'NULL'
        else:
            return match.group()

    def download(self,savetype,url,sign=''):
        try:
            content = self.getResponse(url)
            filename = sign + url[7:].replace('/','_')
            self.setfilename(filename)

            # wb: 非文本文  w+: 文本文件
            openType = 'wb' if savetype else 'w+'
            with open(self.__file_name, openType) as code:
                code.write(content)
        except:
            return -1

        if '.gif' == filename[-4:]:
            return self.convertJif2Png(filename)

        return filename

    def dfsTags(self,tags,depth=0):
        if depth == 0:
            self.taglist = []
        if tags == None:
            return
        if tags.string == None:
              for tag in tags:
                   self.dfsTags(tag,depth+1)
        else:
            ss = (str)(tags.string).strip()
            if ss.replace('\n',''):
                 self.taglist.append(ss)

    def formatString(self,s):
        return u'' + s.strip().replace('<br/>','').replace('<br />','').replace('\n','')

    def stringToDict(self, s):
        #s like "{a:'b',c:'d'}" or "{'a':'b',c:'d'}" or "{'a':b,c:d}"

        dic = {}
        s = s.strip()[1:-1]
        slist = s.split(',')
        for ss in slist:
            i = 0
            for i in range(0,len(ss)):
                if ss[i] == ':':
                    break
            s1 = ss[:i].strip()
            s2 = ss[i+1:].strip()
            # 如果key 已经是"a" or 'a'的形式 则去掉已配对的"" or '' 然后加入dict
            if (s1[0] == "'" and s1[-1] == "'") or (s1[0] == '"' and s1[-1] == '"'):
                k = s1[1:-1]
            else:
                k = s1
            if (s2[0] == "'" and s2[-1] == "'") or (s2[0] == '"' and s2[-1] == '"'):
                v = s2[1:-1]
            else:
                v = s2
            dic[k] = v
        return dic
