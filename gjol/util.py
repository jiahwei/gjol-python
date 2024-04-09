import os, shutil, json, datetime, requests, re,warnings
from lxml import etree, html
from bs4 import BeautifulSoup
from functools import cmp_to_key

# from bs4FindFun import bs4FindFun
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}
defaultFloderPath = "./archives"


def has_date(string):
    """string 是否是日期"""
    date_pattern = (
        r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\w{3}\s\d{1,2},?\s\d{4}"
    )
    match = re.search(date_pattern, string)
    if match:
        return True
    else:
        return False


def compDateTime(x, y):
    """日期比较大小"""
    isDS_Store = ".DS_Store" in x or ".DS_Store" in y
    if isDS_Store:
        return -1
    else:
        dateX = datetime.datetime.strptime(x, "%Y-%m-%d")
        dateY = datetime.datetime.strptime(y, "%Y-%m-%d")
        if dateX < dateY:
            return 1
        elif dateX > dateY:
            return -1
        else:
            return 0


def getDefaultFloderFile():
    """获取archives中的文件名称"""
    floderFiles = os.listdir(defaultFloderPath)
    sortFloderFiles = sorted(floderFiles, key=cmp_to_key(compDateTime))
    return sortFloderFiles


def getDateFormFile(filePath):
    """从html中读取日期，作为archives下文件夹的名称
    payload:
        filePath:原始html文件路径
    return:
        string,日期
    """
    with open(filePath, "r", encoding="utf-8") as f:
        content = f.read()
        f.close()
    contentHtml = etree.HTML(content) # type: ignore
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
    contentHtml = etree.HTML(content) # type: ignore
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
                html.tostring(partent[0], encoding="utf-8").decode("utf-8") # type: ignore
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

def categorizationByBs4(path):
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
        }
    ]
    typeList = []
    lastChildFirstTest = None
    contentArr = []
    totalLen = 0
    otherInfo = {"date": "", "authors": ""}
    for ruler in findRules:
        typeList = soup.find_all(
            name=ruler["name"], style=ruler["style"], string=ruler["string"]
        )
        if len(typeList) > 0:
            break
    if len(typeList) == 0:
        warnText = "捕获规则失效：{}".format(path)
        warnings.warn(warnText)
        textList = list(text for text in soup.stripped_strings)
        allText = "".join(textList)
        totalLen = len(allText)
        return {"totalLen": totalLen, **otherInfo, "contentArr": contentArr}
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
            otherInfo["date"] = "{}-{}-{}".format(year, month, day)
            otherInfo["authors"] = textArr.pop()
            #如果存在就删除礼貌用语
            if textArr[len(textArr) - 1] == '祝大家游戏愉快！':
                textArr.pop()
            if textArr[len(textArr) - 1] == '维护期间给您带来的不便，敬请谅解。':
                textArr.pop()            
        allText = "".join(textArr)
        info = {
            "name": typeName.replace("☆", ""),
            "content": allText,
            "leng": len(allText),
        }
        totalLen = totalLen + info["leng"]
        contentArr.append(info)
        lastChildFirstTest = typeName
    return {"totalLen": totalLen, **otherInfo, "contentArr": contentArr}


def saveDesc(path, obj):
    """保存公告的描述信息，如果json文件存在，就先读取再合并保存，不存在则新建json文件。
    payload:
        path:desc文件路径，不存在会新建。
        obj:新增的数据
    """
    source = {}
    isHaveJson = os.path.exists(path)
    if isHaveJson:
        with open(path, "r") as f:
            source = json.load(f)
            f.close()
    source.update(obj)
    with open(path, "w") as f:
        json.dump(source, f, ensure_ascii=False)
        f.close()


def getFirstArchives(floderPath=defaultFloderPath):
    """从Archive文件夹中读取最新的一条公告"""
    floderFiles = os.listdir(floderPath)
    sortFloderFiles = sorted(floderFiles)
    jsonFilePath = "{}/{}/desc.json".format(
        floderPath, sortFloderFiles[len(sortFloderFiles) - 1]
    )
    isHaveJson = os.path.exists(jsonFilePath)
    if isHaveJson:
        with open(jsonFilePath, "r") as f:
            source = json.load(f)
            f.close()
    else:
        raise ValueError("Archive中最新的公告信息里不存在desc.josn")
    print(source)
    return source


def getNoticeInfo(url, firstNoticeDate):
    """获取公告列表中的全部公告信息
    payload:
        url:公告列表的URL
        firstNoticeDate:已保存第一条公告的日期
    """
    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")
    allList = soup.find("div", class_="list_box").find_all("li") # type: ignore
    res = []
    for li in allList:
        infoForA = li.a
        infoForTime = li.span
        date = datetime.datetime.strptime(infoForTime.string, "%Y-%m-%d")
        if date > firstNoticeDate:
            info = {
                "name": infoForA.attrs["title"],
                "href": infoForA.attrs["href"],
                "date": infoForTime.string,
            }
            res.append(info)
        else:
            print(infoForA.attrs["title"])
    return res
