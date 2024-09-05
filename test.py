import os, json, sqlite3, sys
import sys

sys.path.append(".")
sys.path.append("./util")

from constants import DEFAULT_SQLITE_PATH

conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
cur = conn.cursor()

# cur.execute("ALTER TABLE bulletin RENAME COLUMN DATE TO bulletin_date;")
# cur.execute("ALTER TABLE bulletin RENAME COLUMN totalLen TO total_leng;")
# cur.execute("ALTER TABLE bulletin RENAME COLUMN orderID TO order_id;")
# cur.execute("ALTER TABLE bulletin RENAME COLUMN contentTotalArr TO content_total_arr;")
# cur.execute("ALTER TABLE bulletin RENAME COLUMN NAME TO bulletin_name;")

cur.execute("ALTER TABLE version RENAME COLUMN ID TO id;")
cur.execute("ALTER TABLE version RENAME COLUMN startdate TO start_date;")
cur.execute("ALTER TABLE version RENAME COLUMN enddate TO end_date;")
conn.commit()
conn.close()

# sql_query_all_version = """
# SELECT id,acronyms from version
# """
# cur.execute(sql_query_all_version)
# version_rows = cur.fetchall()
# version_list = [{"id": row[0], "acronyms": row[1], "list": []} for row in version_rows]

# sql_query_bulletin = """
# SELECT ID,DATE,TOTALLEN FROM bulletin
# WHERE VERSION_ID = ?
# ORDER BY TOTALLEN DESC
# """
# for version in version_list:
#     cur.execute(sql_query_bulletin, (version["id"],))
#     bulletin_row = cur.fetchall()
#     formatted_data = [
#         {"id": id, "date": date, "totalLen": totalLen, "order": i + 1}
#         for i, (id, date, totalLen) in enumerate(bulletin_row)
#     ]
#     sql_updata_order = """
#     UPDATE bulletin SET orderID = ? WHERE ID = ?;
#     """
#     for bulletin in formatted_data:
#         cur.execute(sql_updata_order,(bulletin['order'],bulletin['id'],))
# conn.commit()
# conn.close()

