import json
import requests
from requests.exceptions import RequestException
import re
import time
from fake_useragent import UserAgent
#import openpyxl
import os
import pypinyin

def hp(word):
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s += ''.join(i)
    return s

def get_header():
    location = os.getcwd() + '/fake_useragent.json'
    isExists=os.path.exists(location)
    if isExists:
        ua = UserAgent(path=location)
    else:
        ua = UserAgent()
    headers = {
        'User-Agent':ua.random
    }
    return headers

def mkdir(path):
    path=path.strip()
    path=path.rstrip("\\")
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print(path+'\t创建成功')
        return True
    else:
        print(path+'\t目录已存在')
        return False

def delfile(path):
    isExists=os.path.exists(path)
    if not isExists:
        return True
    else:
        print(path + '已存在')
        choice = input('回车跳过；其它输入覆盖： ')
        if choice:
            os.remove(path)
            print('已删除原文件')
            return True
        else:
            print('已跳过该文件')
            return False

def get_one_page(url):
    i=1
    while i<=3:
        try:
            response = requests.get(url,headers=get_header(),timeout=5)
            return response.text
        except requests.exceptions.RequestException:
            i += 1
    if not response:
        print('get_one_page ERROR')
        return False
    else:
        pass

def get_all_pages(urlinput, hospital):
    i = 1
    one_html = get_one_page(url = 'https://www.haodf.com/hospital/'+urlinput+'/menzhen_' + str(i) + '.htm')
    endpage = hospital_endpage(one_html)
    all_pages = ''
    print('正在获取' + hospital + '的页面,共' + str(endpage) + '页')
    while i <= endpage:
        print('正在获取' + 'https://www.haodf.com/hospital/'+urlinput+'/menzhen_' + str(i) + '.htm')
        one_html = get_one_page(url = 'https://www.haodf.com/hospital/'+urlinput+'/menzhen_' + str(i) + '.htm')
        times = 1
        while times <= 3:
            try:
                next(doctor_info(one_html))
                all_pages += one_html
                i += 1
                break
            except StopIteration:
                print('one_html:\n' + one_html)
                one_html = get_one_page(url = 'https://www.haodf.com/hospital/'+urlinput+'/menzhen_' + str(i) + '.htm')
                print('Retry getting page: ' + str(i) + ' for the ' + str(times) + ' time(s)')
                times += 1
        if times == 4:
            i += 1
        else:
            pass
    return all_pages

def doctor_info(html):
    pattern = re.compile('<td class="tdnew_a">\s*<li><a target="_blank" href='
                         +'"//(.{,100})" ' #匹配主页，item0
                         +'title="(.{2,13})" ' #匹配姓名，item1
                         +'class="name">.{2,13}</a>\s*'
                         +'(<a.{,250}></a>\s*)?' #匹配可能存在的其它页面，item2不显示
                         +'(<br />(.{,6})\s*)?' #匹配职称，item3不显示,item4可选
                         +'(<br/>(.{,4})\s*)?' #匹配教职，item5不显示,item6可选
                         +'<br/><a href=".{,80}">(.*?)' #匹配科室，item7
                         +'</a>\s*</li>\s*</td>\s*'
                         +'<td class="tdnew_b">.*?</td>\s*'
                         +'<td class="tdnew_c">.*?</td>\s*'
                         +'<td class="tdnew_d">.*?</td>', re.S)
    doctors = re.findall(pattern, html)
    for doctor in doctors:
        doc_list = list(doctor)
        for i in range(0,8):
            if doc_list[i] == '':
                doc_list[i]='无'
        yield {
            '姓名':doc_list[1],
            '拼音':hp(doc_list[1]),
            '职称':doc_list[4].strip(),
            '教职':doc_list[6].strip(),
            '科室':doc_list[7],
            '主页':doc_list[0]
        }

def region_exist(html):
    pattern = re.compile('暂无医院信息', re.S)
    existence = re.findall(pattern, html)
    if existence:
        return False
    else:
        return True

def hospital_endpage(html):
    pattern = re.compile('<a class="p_text" rel="true">共&nbsp;(.{1,3})&nbsp;页</a>', re.S)
    endpage = re.findall(pattern, html)
    if endpage:
        return int(endpage[0])
    else:
        return 1

def hospital_info(html, mode):
    if mode == 1:
        pattern = re.compile('<li>\s*<a href="/hospital/(.{,50}).htm"\s*'
                             +'target="_blank">(.{,20})</a>\s*<span>\s*'
                             +'(\((.{2})(, 特色:(.*?))?\)\s*)?</span>\s*</li>', re.S)
        hospitals = re.findall(pattern, html)
        for hospital in hospitals:
            hos_info = list(hospital)
            for i in range(0,6):
                if hos_info[i] == '':
                    hos_info[i]='无'
            yield {
                '网址':hos_info[0],
                '医院':hos_info[1],
                '级别':hos_info[3],
                '特色':hos_info[5]
            }
    elif mode == 2:
        pattern = re.compile('<a href="//.*?">好大夫在线</a> &gt; <a\s*'
                         +'href="//.*?">医院</a> &gt; <a\s*'
                         +'href="//.*?">(.*?)</a> &gt;\s*'
                         +'门诊时间\s*</div>', re.S)
        hospital = re.findall(pattern, html)
        yield {
            '医院':hospital[0]
        }
        

def doctor_number(html):
    pattern = re.compile('<td class="white">\(科室(.{,3})个, 大夫(.{,4})人\)</td>', re.S)
    doctors = re.findall(pattern, html)
    doctor = doctors[0]
    if doctor:
        return int(doctor[1])
    else:
        print('Failed')
        print(type(doctor))
        print(doctor)
        
def write_to_file(content, path):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')

def main():
    print('Version: 1.0\nLast Modification:11/19/2019 18:00')
    province='/' + input('输入省份/直辖市：')
    city='/' + input('输入城市/区：')
    if city == '/':
        city=''
    mode=int(input('输入1获取整个城市/区的数据;\n输入2获取特定医院数据:'))
    directory='./好大夫'+province+city+'/'
    mkdir(directory)
    if mode == 1:
        province=(province.rstrip('省')).rstrip('市')
        city=(city.rstrip('区')).rstrip('市')
        url='https://www.haodf.com/yiyuan'+hp(province)+hp(city)+'/list.htm'
        html=get_one_page(url)
        while not region_exist(html):
            print('查询无结果!')
            province=input('启用辅助拼音模式：\n输入省：')
            city=input('输入市：')
            province=(province.rstrip('sheng')).rstrip('shi')
            city=(city.rstrip('qu')).rstrip('shi')
            url='https://www.haodf.com/yiyuan/'+hp(province)+'/'+hp(city)+'/list.htm'
            html=get_one_page(url)
                
    elif mode == 2:
        urlinput = input('输入医院网址特征段:')
        url = 'https://www.haodf.com/hospital/'+urlinput+'/menzhen.htm'
        html = get_one_page(url)

    for hos_info in hospital_info(html, mode = mode):
        i = 1
        if mode == 1:
            urlinput = hos_info['网址']
        else:
            pass
        url = 'https://www.haodf.com/hospital/'+urlinput+'/menzhen.htm'
        times = 1
        while times <= 3:
            try:
                html = get_one_page(url)
                doctors = doctor_number(html)
                break
            except IndexError:
                print('Getting number of doctors Error.')
                print('Retrying: ' + str(times) + 'time(s)')
                times += 1
        path = directory + hos_info['医院'] + '.txt'
        choice = delfile(path)
        if choice:
            print(hos_info)
            write_to_file(content=hos_info, path=path)
            all_pages = get_all_pages(urlinput = urlinput, hospital = hos_info['医院'])
            num_test = 0
            for doc_list in doctor_info(all_pages):
                print(doc_list)
                num_test += 1
                write_to_file(content=doc_list, path=path)
            if num_test == doctors:
                print('right!')
            else:
                print('num_test:' + str(num_test))
                print('doc_number:' + str(doctors))
                print('Wrong!Please check manually.')
        else:
            print(hos_info['医院'] + '已被跳过')

if __name__ == '__main__':
    main()
