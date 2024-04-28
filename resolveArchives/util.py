import os, shutil, json, datetime, requests, re, warnings, time, random, sqlite3
from lxml import etree, html
from bs4 import BeautifulSoup
from functools import cmp_to_key
from typing import Union, List, Optional
from pydantic import BaseModel
from utilType import ArchiveDesc, NoticeInfo, Content_Completeness, Content, ReleaseInfo
from datetime import date, datetime, timedelta
from utilSqlite import insert_archive_desc, DefaultSqlitePath

import logging

logging.basicConfig(
    filename="app.log", filemode="w", format="%(name)s - %(levelname)s - %(message)s"
)

# from bs4FindFun import bs4FindFun
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}
DefalutFloderPath = "./archives"
DefaultTotalPath = "./total/bulletin.json"
BASEURL = "http://gjol.wangyuan.com/"


def has_date(string: str):
    """string 是否是日期"""
    date_pattern = (
        r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\w{3}\s\d{1,2},?\s\d{4}"
    )
    match = re.search(date_pattern, string)
    if match:
        return True
    else:
        return False


def comp_datetime(x, y):
    """日期比较大小"""
    isDS_Store = ".DS_Store" in x or ".DS_Store" in y
    if isDS_Store:
        return -1
    else:
        dateX = datetime.strptime(x, "%Y-%m-%d")
        dateY = datetime.strptime(y, "%Y-%m-%d")
        if dateX < dateY:
            return 1
        elif dateX > dateY:
            return -1
        else:
            return 0


def get_default_floder_file():
    """获取archives中的文件名称"""
    floderFiles = os.listdir(DefalutFloderPath)
    sortFloderFiles = sorted(floderFiles, key=cmp_to_key(comp_datetime))
    return sortFloderFiles


def get_date_form_file(filePath):
    """从html中读取日期，作为archives下文件夹的名称
    payload:
        filePath:原始html文件路径
    return:
        string,日期
    """
    with open(filePath, "r", encoding="utf-8") as f:
        content = f.read()
        f.close()
    contentHtml = etree.HTML(content)  # type: ignore
    allElementList = contentHtml.xpath("//div[@class='details']//p")
    resolveDate = ""
    for element in reversed(allElementList):
        currentName = element.xpath("string(.)")
        if len(currentName) == 0 | currentName.isspace():
            continue
        resolveDate = currentName.replace("《古剑奇谭网络版》项目组", "").replace(
            "\n", ""
        )
        if not (("年" in resolveDate) & ("月" in resolveDate) & ("日" in resolveDate)):
            raise Exception(
                "{}格式有误,获取的日期格式非法：{}".format(filePath, resolveDate)
            )
        resolveDate = (
            resolveDate.replace("年", "-").replace("月", "-").replace("日", "")
        )
        resolveDate = "".join(resolveDate.split())
        dateArr = resolveDate.split("-")
        year = dateArr[0]
        month = "0{}".format(dateArr[1]) if len(dateArr[1]) < 2 else dateArr[1]
        day = "0{}".format(dateArr[2]) if len(dateArr[2]) < 2 else dateArr[2]
        resolveDate = "{}-{}-{}".format(year, month, day)
        break
    if not has_date(resolveDate):
        raise Exception(
            "{}格式有误,获取的日期格式非法：{}".format(filePath, resolveDate)
        )
    return resolveDate


def get_date_form_NoticeInfo(notice: NoticeInfo):
    """从公告信息里取得公告的时间，从date中取年份，从公告标题中取日和月
    版本更新公告标题中没有日和月 返回空

    Args:
        notice (NoticeInfo): 公告信息

    Returns:
        str: 公告的日期
    """
    year = notice.date[:4]
    try:
        month, day = re.findall(r"\d+", notice.name.split("》")[1][:5])
        new_date = f"{year}-{int(month):02d}-{int(day):02d}"
    except:
        new_date = ""
    return new_date


def categorization(path):
    """从content.html中分类内容
    payload:
        name:content.html文件路径
    return:
        obj:分类结果
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        f.close()
    contentHtml = etree.HTML(content)  # type: ignore
    # 通过小标题的样式切开内容
    xpathRules = [
        "//p/span[@style='color:#ff0000']/span[@style='font-size:16px']",
        "//p/span[@style='color:#ff0000']/span[@style='font-size:18px']",
        "//p/span[@style='font-size:16px']/span[@style='color:#ff0000']",
        "//p//span[@style='font-size:16px']/span[@style='color:#ff0000']",
        "//p//span[@style='font-size:18px']/span[@style='color:#ff0000']",
        "//p//span[@style='font-size:18px']",
        "//p//span[@style='color:#ff0000']/span[@style='font-size:16px']",
        "//p/strong",
    ]
    result = []
    for ruler in xpathRules:
        result = contentHtml.xpath(ruler)
        if len(result) > 0:
            break
    if len(result) == 0:
        raise Exception("捕获规则失效：{}".format(path))
    resolveResult = []
    lastResultLength = 0
    totalLen = 0
    for child in reversed(result):
        currentName = child.xpath("string(.)")
        print("片段为{}".format(currentName))
        # partent = child.xpath("../..")
        partent = child.xpath("..")
        print(
            "根节点为{}".format(
                html.tostring(partent[0], encoding="utf-8").decode("utf-8")  # type: ignore
            )
        )
        pathQuery = "following-sibling::node()/text()"
        # pathQuery = "following::node()/text()"
        # typeContent = partent[0].xpath(pathQuery)
        typeContent = partent[0].xpath(pathQuery)
        print("根节点后续内容为为{}".format(typeContent))
        resolveArr = []
        resolveArr = typeContent[0 : len(typeContent) - lastResultLength]
        lastResultLength = len(typeContent)
        obj = {
            "name": currentName.replace("☆", ""),
            "content": "".join(resolveArr),
        }
        obj["content"] = "".join(obj["content"].split())
        obj["length"] = len(obj["content"])
        totalLen = totalLen + obj["length"]
        resolveResult.append(obj)
    return {"totalLen": totalLen, "contentArr": resolveResult}


def categorization_by_bs4(path: str, noticeInfo: NoticeInfo):
    """从content.html中分类内容

    Args:
        path (str): content.html文件路径
        noticeInfo (NoticeInfo): 公告信息

    Returns:
        ArchiveDesc: 公告desc信息
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        f.close()
    soup = BeautifulSoup(content, "html5lib")
    # 通过小标题分开内容
    findRules = [
        {
            "name": "span",
            "style": lambda value: value and "font-size" in value and "18px" in value,
            "string": None,
        },
        {
            "name": "span",
            "style": lambda value: value and "font-size" in value and "16px" in value,
            "string": None,
        },
    ]
    typeList = []
    lastChildFirstTest = None
    notice_date: str = get_date_form_NoticeInfo(notice=noticeInfo)
    notice_authors: str = ""
    categorization: ArchiveDesc = ArchiveDesc(name=noticeInfo.name)
    contentArr = []
    contentTotalArr = []
    totalLen = 0
    for ruler in findRules:
        typeList = soup.find_all(
            name=ruler["name"], style=ruler["style"], string=ruler["string"]
        )
        if len(typeList) > 0:
            break
    if len(typeList) == 0:
        warnText = "捕获规则失效：{}".format(path)
        warnings.warn(warnText)
        logging.warning(warnText)
        textList = list(text for text in soup.stripped_strings)
        allText = "".join(textList)
        totalLen = len(allText)
        if not len(notice_date) == 0:
            notice_date_warn = "日期无效：{}".format(path)
            warnings.warn(notice_date_warn)
            logging.warning(notice_date_warn)
        categorization.date = notice_date
        categorization.totalLen = totalLen
        return categorization
        # raise Exception("捕获规则失效：{}".format(path))
    for child in reversed(typeList):
        # 小标题的父级p标签
        parentPTag = child.find_parent("p")
        typeName = parentPTag.get_text(strip=True)
        textArr = []
        for nextPTage in parentPTag.next_siblings:
            textList = list(text for text in nextPTage.stripped_strings)
            isContinue = False
            if len(textList) == 0:
                continue
            if not isContinue and textList[0] == lastChildFirstTest:
                isContinue = True
                break
            textArr.extend(textList)
        if lastChildFirstTest is None:
            # 取出公告末尾的时间和作者
            timeText = textArr.pop()
            timeText = timeText.replace("年", "-").replace("月", "-").replace("日", "")
            timeText = "".join(timeText.split())
            dateArr = timeText.split("-")
            year = dateArr[0]
            month = "0{}".format(dateArr[1]) if len(dateArr[1]) < 2 else dateArr[1]
            day = "0{}".format(dateArr[2]) if len(dateArr[2]) < 2 else dateArr[2]
            notice_authors = textArr.pop()
            notice_date_from_file = "{}-{}-{}".format(year, month, day)
            categorization.authors = notice_authors
            if notice_date != notice_date:
                notice_date_warn = (
                    "日期不一致：{}，get_date_form_NoticeInfo：{},公告末尾{}".format(
                        path, notice_date, notice_date_from_file
                    )
                )
                warnings.warn(notice_date_warn)
                logging.warning(notice_date_warn)
            categorization.date = notice_date
            # 如果存在就删除礼貌用语
            if textArr[len(textArr) - 1] == "祝大家游戏愉快！":
                textArr.pop()
            if textArr[len(textArr) - 1] == "维护期间给您带来的不便，敬请谅解。":
                textArr.pop()
        allText = "".join(textArr)
        info = Content(name=typeName.replace("☆", ""), leng=len(allText))
        totalLen = totalLen + info.leng
        info_by_content = Content_Completeness(
            name=info.name, leng=info.leng, content=allText
        )
        contentArr.append(info_by_content)
        contentTotalArr.append(info)
        lastChildFirstTest = typeName

    categorization.totalLen = totalLen
    categorization.contentArr = contentArr
    categorization.contentTotalArr = contentTotalArr
    return categorization


def save_desc(path: str, obj: ArchiveDesc):
    """保存公告的描述信息，如果json文件存在，就先读取再合并保存，不存在则新建json文件

    Args:
        path (str): desc文件路径，不存在会新建
        obj (ArchiveDesc): ArchiveDesc的实例
    """
    source = {}
    isHaveJson = os.path.exists(path)
    if isHaveJson:
        with open(path, "r") as f:
            source = json.load(f)
            f.close()
    source.update(obj.model_dump(exclude_none=True))
    with open(path, "w") as f:
        json.dump(source, f, ensure_ascii=False)
        f.close()


def get_first_archives(floderPath: str = DefalutFloderPath):
    """从Archive文件夹中读取最新的一条公告"""
    floderFiles = os.listdir(floderPath)
    sortFloderFiles = sorted(floderFiles)
    jsonFilePath = "{}/{}/desc.json".format(
        floderPath, sortFloderFiles[len(sortFloderFiles) - 1]
    )
    isHaveJson = os.path.exists(jsonFilePath)
    if isHaveJson:
        with open(jsonFilePath, "r") as f:
            source: ArchiveDesc = json.load(f)
            f.close()
    else:
        raise ValueError("Archive中最新的公告信息里不存在desc.josn")
    print(source)
    return source


def get_notice_info(url: str, firstNoticeDate: date):
    """获取公告列表中的全部公告信息

    Args:
        url (str): 公告列表的URL
        firstNoticeDate (date): 已保存第一条公告的日期

    Returns:
        List[NoticeInfo]: 公告列表中的公告信息
    """
    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")
    allList = soup.find("div", class_="list_box").find_all("li")  # type: ignore
    resList: List[NoticeInfo] = []
    for li in allList:
        infoForA = li.a
        infoForTime = li.span
        date = datetime.strptime(infoForTime.string, "%Y-%m-%d")
        if date > firstNoticeDate:
            info = NoticeInfo(
                name=infoForA.attrs["title"],
                href=infoForA.attrs["href"],
                date=infoForTime.string,
            )
            resList.append(info)
        else:
            print(infoForA.attrs["title"])
    return resList


def folder_exists(folder_name: str, directory: str = DefalutFloderPath):
    """判断 folder_name 是否存在于文件夹 directory 中

    Args:
        folder_name (str): 子文件夹名称
        directory (str, optional): 父文件夹名称，默认 DefalutFloderPath.

    Returns:
        bool: _description_
    """
    folder_path = os.path.join(directory, folder_name)
    return os.path.exists(folder_path)


def download_file(noticeInfo: NoticeInfo):
    """下载公告文件，保存到archives下，以日期作为文件夹名称

    Args:
        noticeInfo (NoticeInfo): 公告信息
    Returns:
        str: 下载公告的conent文件的路径
    """
    floderName = noticeInfo.date
    url = noticeInfo.href.replace("/z/../", BASEURL)
    is_have_file = folder_exists(floderName)
    source_file_name: str = "{}/{}/source.html".format(DefalutFloderPath, floderName)
    content_file_name: str = "{}/{}/content.html".format(DefalutFloderPath, floderName)
    if not is_have_file:
        print(f"下载公告日期{floderName}")
        res = requests.get(url, headers=header).text
        soup = BeautifulSoup(res, "lxml")

        directory = os.path.dirname(source_file_name)
        os.makedirs(directory, exist_ok=True)
        with open(source_file_name, "w", encoding="utf-8") as f:
            f.write(str(soup))
            f.close()

        # 过滤不需要的标签
        for excludedDivName in ["more_button", "bdsharebuttonbox"]:
            excluded_div = soup.find("div", {"class": excludedDivName})
            if excluded_div is not None:
                excluded_div.extract()
        excluded_tags = soup.select("script")
        for tag in excluded_tags:
            tag.extract()
        details = soup.find("div", class_="details")
        with open(content_file_name, "w", encoding="utf-8") as f:
            f.write(str(details))
            f.close()
    return content_file_name


def download_and_resolve_notice(noticeList: List[NoticeInfo], is_resolve: bool = True):
    """下载公告,支持调用 categorization_by_bs4 生成desc.josn文件和更新数据库

    Args:
        noticeList (List[NoticeInfo]): 公告信息组成的List
        is_resolve (bool, optional): 默认生成desc.josn文件和更新数据库
    """
    for i, noticeInfo in enumerate(noticeList):
        name = noticeInfo.name
        isNoticeDownLoad: bool = not folder_exists(noticeInfo.date)
        filterName = (
            "更新维护公告" in name
            or "职业调整公告" in name
            or "职业技能改动公告" in name
        )
        if filterName and isNoticeDownLoad:
            sleeptime = random.randint(10, 40)
            file_path = download_file(noticeInfo)
            if is_resolve:
                categorizationInfo = categorization_by_bs4(file_path, noticeInfo)
                desc_file_name: str = "{}/{}/desc.json".format(
                    DefalutFloderPath, noticeInfo.date
                )
                save_desc(desc_file_name, categorizationInfo)
                insert_archive_desc(categorizationInfo)
            print(f"第{i}次循环,{name},等待{time.ctime()}秒")
            time.sleep(sleeptime)
            print(f"第{i}次循环结束,{time.ctime()}")
        else:
            print(f"第{i}次循环,{name},不是公告，不需要处理,跳过,{time.ctime()}")


def merge_requirements(*args):
    all_requirements = []
    for file in args:
        with open(file, "r") as f:
            all_requirements += f.read().splitlines()

    # 去除重复项
    unique_requirements = list(set(all_requirements))

    # 写入新的 requirements 文件
    with open("combined_requirements.txt", "w") as f:
        for requirement in unique_requirements:
            f.write(requirement + "\n")


def adjust_to_nearest_thursday(date_str):
    """把非周四的日期调整到最近的周四

    Args:
        date_str (str): 非周四的日期

    Returns:
        str: 最近的周四
    """
    date_format = "%Y-%m-%d"
    date = datetime.strptime(date_str, date_format)
    weekday = date.weekday()

    if weekday < 3:
        # If the date is before Thursday, go forward to the next Thursday
        date += timedelta(days=(3 - weekday))
    elif weekday > 3:
        # If the date is after Thursday, go back to the previous Thursday
        date -= timedelta(days=(weekday - 3))

    return date.strftime(date_format)


def rename_no_thursday(date_str):
    date_format = "%Y-%m-%d"
    date = datetime.strptime(date_str, date_format)
    weekday = date.weekday()

    if weekday == 3:
        return
    thurs_day = adjust_to_nearest_thursday(date_str)
    thurs_day_date = datetime.strptime(date_str, date_format)
    full_dir_path = "{}/{}".format(DefalutFloderPath, date_str)
    full_thurs_dir_path = "{}/{}".format(DefalutFloderPath, thurs_day)
    if os.path.exists(full_dir_path):

        desc_file_name = "{}/{}/desc.json".format(DefalutFloderPath,date_str)
        with open(desc_file_name, "r") as f:
            source = json.load(f)
            f.close()
        source['date'] = thurs_day
        with open(desc_file_name, "w") as f:
            json.dump(source, f, ensure_ascii=False)
            f.close()

        os.rename(full_dir_path, full_thurs_dir_path)

        conn = sqlite3.connect(DefaultSqlitePath)
        cur = conn.cursor()
        sql_update_query = """
        UPDATE bulletin
        SET date = ?
        WHERE date = ?;
        """
        cur.execute(sql_update_query,(thurs_day,date_str))
        conn.commit()
        conn.close()

        print(f"文件夹 '{full_dir_path}' 已经被重命名为 '{full_thurs_dir_path}'")
    else:
        print(f"文件夹 '{full_dir_path}' 不存在")


def download_reslease():
    """下载版本数据"""
    base_url = "https://gjol.wangyuan.com/info/huod/version{}.shtml"
    resList: List[ReleaseInfo] = []
    for i in range(3):
        url = (
            base_url.format(i)
            if i != 0
            else "https://gjol.wangyuan.com/info/huod/version.shtml"
        )
        res = requests.get(url, headers=header).text
        soup = BeautifulSoup(res, "lxml")
        allList = soup.find("div", class_="group_list").find_all("li")  # type: ignore
        for li in allList:
            name = li.span.string
            time = li.p.i.string
            date = datetime.strptime(time, "%Y.%m.%d")
            res_date = date.strftime("%Y-%m-%d")
            resList.append(
                ReleaseInfo(name=name, start_date=res_date, end_date="", acronyms="")
            )
    return resList
