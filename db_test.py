import sqlite3
import pandas as pd

conf = sqlite3.connect('../database/test.db', check_same_thread=False)
cur = conf.cursor()

def to_pandas(db_result):
    rows =db_result.fetchall()
    cols = [column[0] for column in db_result.description]
    df = pd.DataFrame.from_records(data=rows, columns =cols)
    return df

for table_name in ['CheckDetail']:
    result = cur.execute(f'SELECT * FROM {table_name}')
    df = to_pandas(result)
    print(table_name)
    # print(df)
    if df.shape[0] == 0:
        print('zero table')
    for i in df.iterrows():
        # print(i[1]['total_idx'])
        values= (i[1]['total_idx'], 1)
        cur.execute(f"insert into EditDetail(total_idx, file_idx) values{values}")
        cur.execute("commit;")

result = cur.execute(f'SELECT * FROM EditDetail')
df = to_pandas(result)
print(df.shape)