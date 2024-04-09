"""
对archives中存在的公告文件进行处理。不发起网络请求
产生的结果放入desc.json中
"""

from util import defaultFloderPath
import os
import time
from util import getDefaultFloderFile, categorization, saveDesc,categorizationByBs4


# 获取archives
floderFiles = getDefaultFloderFile()
print(floderFiles)
for floderName in floderFiles:
    if ".DS_Store" in  floderName:
        continue
    fileName = "{}/{}/content.html".format(defaultFloderPath, floderName)
    descFileName = "{}/{}/desc.json".format(defaultFloderPath, floderName)
    if os.path.exists(fileName):
        start = time.perf_counter()
        categorizationInfo = categorizationByBs4(fileName)
        saveDesc(descFileName, categorizationInfo)
        end = time.perf_counter()
        print("{},用时{}毫秒".format(floderName,(end - start) * 1000))


# floderName = '2018-10-10'
# floderName = '2020-09-30'
# print(floderName)
# fileName = "{}/{}/content.html".format(defaultFloderPath, floderName)
# descFileName = "{}/{}/desc.json".format(defaultFloderPath, floderName)
# if os.path.exists(fileName):
#     # categorizationInfo = categorization(fileName)
#     categorizationInfo = categorizationByBs4(fileName)
#     # print(completeHTML(fileName))
    
#     print(categorizationInfo)
#     # saveDesc(descFileName, categorizationInfo)
