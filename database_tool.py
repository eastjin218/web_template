import json, os, glob
import sqlite3
import pandas as pd

class DatabaseApi():
    def __init__(self, db_path):
        self.db_path = db_path
        self.cur = self.connect_db()
        try:
            self.init_table()
        except:
            pass
        
    def connect_db(self):
        conf = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conf.cursor()
        print('DataBase connection Done!!')
        return cur

    def init_table(self):
        self.cur.execute('''
            CREATE TABLE Filename(
        file_idx integer not null primary key autoincrement,
        name text,
        type text
        );
        ''')
        self.cur.execute('''
            CREATE TABLE ManualDetail(
        detail_idx integer not null primary key autoincrement,
        file_idx integer,
        sent text,
        page_num text
        );
        ''')
        self.cur.execute('''
            CREATE TABLE CheckDetail(
        total_idx integer not null primary key autoincrement,
        no text,
        detail_E text,
        detail_K text,
        stand_sent text
        );
        ''')
        self.cur.execute('''
            CREATE TABLE PredictDetail(
        predict_idx integer not null primary key autoincrement,
        total_idx integer,
        file_idx integer,
        model_idx integer,
        sent1 integer,
        sent2 integer,
        sent3 integer,
        simility_score1 float,
        simility_score2 float,
        simility_score3 float
        );
        ''')
        self.cur.execute('''
            CREATE TABLE EditDetail(
        edit_idx integer not null primary key autoincrement,
        total_idx integer,
        file_idx integert,
        save_datetime DATETIME DEFAULT (DATETIME('now', 'localtime')),
        correct_check boolean,
        correct_sent text,
        correct_page_num integer,
        inspector text
        );
        ''')
        self.cur.execute('''
            CREATE TABLE AiModel(
        model_idx integer not null primary key autoincrement,
        model_name text,
        datetime DATETIME DEFAULT (DATETIME('now', 'localtime')),
        top_1_avg_sim float
        );
        ''')
        

    def to_pandas(self, db_result):
        rows =db_result.fetchall()
        cols = [column[0] for column in db_result.description]
        df = pd.DataFrame.from_records(data=rows, columns =cols)
        return df

    def read_db_table(self, table_name):
        result = self.cur.execute(f'SELECT * FROM {table_name}')
        return self.to_pandas(result)

    def get_no_checkdetail(self):
        result = self.cur.execute(f"SELECT no FROM CheckDetail")
        return self.to_pandas(result)
    
    def get_sort_by_no_checkdetail(self, value):
        result = self.cur.execute(f"SELECT * FROM CheckDetail WHERE no IN {value}")
        return self.to_pandas(result)
    
    def get_checkdetail(self, values):
        result = self.cur.execute(f"SELECT * FROM CheckDetail WHERE file_idx = {values}")
        return self.to_pandas(result)

    def get_manualdetail(self, values):
        result = self.cur.execute(f"SELECT * FROM ManualDetail WHERE file_idx = {values}")
        return self.to_pandas(result)

    def get_editdetail(self, m_idx, c_idx):
        result = self.cur.execute(f"SELECT * FROM EditDetail WHERE file_idx={m_idx} AND total_idx in {c_idx}")
        return self.to_pandas(result)


    def input_filename(self, values):
        self.cur.execute(f"insert into Filename(name, type) values{values}")
        self.cur.execute("commit;")

    def input_checkdetail(self, values):
        self.cur.execute(f"insert into CheckDetail(no, detail_E, detail_K, stand_sent) values{values}")
        self.cur.execute("commit;")

    def input_manualdetail(self, values):
        self.cur.execute(f"insert into ManualDetail(file_idx, sent, page_num) values{values}")
        self.cur.execute("commit;")

    def input_predictdetail(self,values):
        self.cur.execute(f"insert into PredictDetail(total_idx, file_idx, model_idx, sent_idx1, sent_idx2, sent_idx3, simility_score1, simility_score2, simility_score3) values{values}")
        self.cur.execute("commit;")

    def input_editdetail(self, values):
        self.cur.execute(f"insert into EditDetail(total_idx, file_idx) values{values}")
        self.cur.execute("commit;")