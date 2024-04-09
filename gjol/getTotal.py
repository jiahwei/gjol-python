"""
对archives中存在的公告 desc.josn 进行统计
"""
import os,json
from util import getDefaultFloderFile
from util import defaultFloderPath,defaultTotalPath

def getTotal():
    with open (defaultTotalPath,"r") as f:
        totalJson = json.load(f)
        f.close()
    return totalJson

def saveDescToTotal(info,ignoreSave = True):
    totalInfo = getTotal()
    if ignoreSave and info["date"] in  totalInfo["map"]:
        # print("ignoreSave,{}".format(info["date"]))
        return
    totalInfo["list"].append(info)
    totalInfo["map"][info["date"]] = info
    with open(defaultTotalPath, "w") as f:
        json.dump(totalInfo, f, ensure_ascii=False)
        f.close()
        

# 获取archives
# floderFiles = getDefaultFloderFile()
# for floderName in floderFiles:
#     if ".DS_Store" in  floderName:
#         continue
#     descFileName = "{}/{}/desc.json".format(defaultFloderPath, floderName)
#     if os.path.exists(descFileName):
#         with open(descFileName, "r") as f:
#             content = json.load(f)
#             if "date" in content:
#                 content.pop('contentArr')
#                 content.pop('name')
#                 content.pop("authors")
#                 saveDescToTotal(content)
#             else:
#                 raise Exception("保存失效，缺失必要参数date：{}".format(content))
#             f.close()

        