from util.nomal import adjust_to_nearest_thursday, rename_no_thursday
from util.type import ArchiveDesc, NoticeInfo, VersionInfo

pendingNoticeTest: list[NoticeInfo] = [
    NoticeInfo(
        name="《古剑奇谭网络版》4月25日更新维护公告",
        href="/z/../2024/04/24/026520.shtml",
        date="2024-04-24",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月25日更新维护通告",
        href="/z/../2024/04/24/026519.shtml",
        date="2024-04-24",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月18日更新维护通告",
        href="/z/../2024/04/17/025520.shtml",
        date="2024-04-17",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月18日更新维护公告",
        href="/z/../2024/04/17/025519.shtml",
        date="2024-04-17",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月11日更新维护公告",
        href="/z/../2024/04/10/025518.shtml",
        date="2024-04-10",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月11日更新维护通告",
        href="/z/../2024/04/10/025517.shtml",
        date="2024-04-10",
    ),
    NoticeInfo(
        name="【网元圣唐】客服电话线路调整通知",
        href="/z/../2024/04/08/025516.shtml",
        date="2024-04-08",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月4日更新维护公告",
        href="/z/../2024/04/03/025515.shtml",
        date="2024-04-03",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》4月4日更新维护通告",
        href="/z/../2024/04/03/025514.shtml",
        date="2024-04-03",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月28日更新维护公告",
        href="/z/../2024/03/27/025512.shtml",
        date="2024-03-27",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月28日更新维护通告",
        href="/z/../2024/03/27/025511.shtml",
        date="2024-03-27",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月21日更新维护公告",
        href="/z/../2024/03/20/025510.shtml",
        date="2024-03-20",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月21日更新维护通告",
        href="/z/../2024/03/20/025509.shtml",
        date="2024-03-20",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月14日更新维护公告",
        href="/z/../2024/03/13/025508.shtml",
        date="2024-03-13",
    ),
    NoticeInfo(
        name="《古剑奇谭网络版》3月14日更新维护通告",
        href="/z/../2024/03/13/025507.shtml",
        date="2024-03-13",
    ),
]

# ("2019-06-17",),


date_is_no_turs = [
    # ("2018-09-05",),
    # ("2018-09-12",),
    # ("2018-09-19",),
    # ("2018-09-26",),
    # ("2018-10-03",),
    # ("2018-10-10",),
    # ("2018-10-17",),
    # ("2018-10-24",),
    # ("2018-10-31",),
    # ("2018-11-07",),
    # ("2018-11-28",),
    # ("2019-06-17",),
    ("2020-06-24",),
    ("2020-09-30",),
    ("2020-10-07",),
    ("2021-09-08",),
    ("2021-09-15",),
    ("2021-09-22",),
    ("2021-09-29",),
    ("2021-10-06",),
    ("2021-10-13",),
    ("2021-10-20",),
    ("2021-10-27",),
    ("2021-11-03",),
    ("2021-11-10",),
    ("2021-11-17",),
    ("2021-11-24",),
    ("2021-12-01",),
    ("2021-12-15",),
    ("2021-12-22",),
    ("2021-12-29",),
    ("2022-01-12",),
    ("2022-01-19",),
    ("2022-01-26",),
    ("2022-02-09",),
    ("2022-02-16",),
    ("2022-02-23",),
    ("2022-03-16",),
    ("2022-03-23",),
    ("2022-03-30",),
    ("2022-04-13",),
    ("2022-04-20",),
    ("2022-05-25",),
    ("2023-03-01",),
    ("2023-03-15",),
    ("2023-03-22",),
    ("2023-03-29",),
    ("2023-04-05",),
    ("2023-04-12",),
    ("2023-04-19",),
    ("2023-04-26",),
    ("2023-05-10",),
    ("2023-05-17",),
    ("2023-05-24",),
    ("2023-05-31",),
    ("2023-06-07",),
    ("2023-06-14",),
    ("2023-06-21",),
    ("2023-06-28",),
    ("2023-07-05",),
    ("2023-07-12",),
    ("2023-07-19",),
    ("2023-07-26",),
    ("2023-08-02",),
    ("2023-08-09",),
    ("2023-08-16",),
    ("2023-08-23",),
]

version_info: list[VersionInfo] = [
    VersionInfo(
        name="暑期资料片 ”共烛天明“", start_date="2023-06-29", end_date="", total=0,acronyms='共烛天明'
    ),
    VersionInfo(
        name="年度版本“凿空浑沦”",
        start_date="2022-12-15",
        end_date="2023-06-28",
        total=0,
        acronyms="凿空浑沦"
    ),
    VersionInfo(
        name="暑期资料片“帝首熠兮”",
        start_date="2022-07-14",
        end_date="2022-12-14",
        total=0,
        acronyms="帝首熠兮"
    ),
    VersionInfo(
        name="春季资料片“明心九天”",
        start_date="2022-04-07",
        end_date="2022-07-13",
        total=0,
        acronyms="明心九天"
    ),
    VersionInfo(
        name="2021年度版本“玉轮铃音”",
        start_date="2021-12-09",
        end_date="2022-04-06",
        total=0,
        acronyms="玉轮铃音"
    ),
    VersionInfo(
        name="三周年资料片“天门终开”",
        start_date="2021-07-29",
        end_date="2021-12-08",
        total=0,
        acronyms="天门终开"
    ),
    VersionInfo(
        name="“月引长刀”资料片", start_date="2020-12-17", end_date="2021-07-28", total=0,acronyms="月引长刀"
    ),
    VersionInfo(
        name="2020年度版本“瀚海惊弦”",
        start_date="2020-07-16",
        end_date="2020-12-16",
        total=0,
        acronyms="瀚海惊弦"
    ),
    VersionInfo(
        name="2020春季资料片“山海飞花”",
        start_date="2020-03-19",
        end_date="2020-07-15",
        total=0,
        acronyms="山海飞花"
    ),
    VersionInfo(
        name="《古剑奇谭三》联动资料片“梦与时空”",
        start_date="2019-11-21",
        end_date="2020-03-18",
        total=0,
        acronyms="梦与时空"
    ),
    VersionInfo(
        name="2019年“正式公测”", start_date="2019-07-11", end_date="2019-11-20", total=0,acronyms="公测(琅泉太华)"
    ),
    VersionInfo(
        name="2019春季版本", start_date="2019-03-14", end_date="2019-07-10", total=0,acronyms="2019春季版本"
    ),
    VersionInfo(
        name="剑鸣流花", start_date="2018-12-20", end_date="2019-03-13", total=0,acronyms="剑鸣流花"
    ),
    VersionInfo(
        name="不删档测试", start_date="2018-08-16", end_date="2018-12-19", total=0,acronyms="不删档测试"
    ),
]


# adjusted_dates = [adjust_to_nearest_thursday(date[0]) for date in date_is_no_turs]
# print(adjusted_dates)

# for date in date_is_no_turs:
#     rename_no_thursday(date[0])
