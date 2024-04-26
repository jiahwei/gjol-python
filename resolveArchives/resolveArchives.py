"""
对archives中存在的公告文件进行处理。不发起网络请求
产生的结果放入desc.json中
"""

from util import DefalutFloderPath
import os
import time
from util import get_default_floder_file, categorization, save_desc,categorization_by_bs4


# 获取archives
# floderFiles = get_default_floder_file()
# print(floderFiles)
# for floderName in floderFiles:
#     if ".DS_Store" in  floderName:
#         continue
#     fileName = "{}/{}/content.html".format(DefalutFloderPath, floderName)
#     descFileName = "{}/{}/desc.json".format(DefalutFloderPath, floderName)
#     if os.path.exists(fileName):
#         start = time.perf_counter()
#         categorizationInfo = categorization_by_bs4(fileName)
#         save_desc(descFileName, categorizationInfo)
#         end = time.perf_counter()
#         print("{},用时{}毫秒".format(floderName,(end - start) * 1000))


# floderName = '2018-10-10'
# floderName = '2023-09-14'
# print(floderName)
# fileName = "{}/{}/content.html".format(DefalutFloderPath, floderName)
# descFileName = "{}/{}/desc.json".format(DefalutFloderPath, floderName)
# if os.path.exists(fileName):
#     # categorizationInfo = categorization(fileName)
#     categorizationInfo = categorization_by_bs4(fileName)
#     # print(completeHTML(fileName))
    
#     print(categorizationInfo)
#     # save_desc(descFileName, categorizationInfo)
