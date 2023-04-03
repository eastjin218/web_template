import os, re
import pandas as pd
import PyPDF2
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from threading import Lock
from werkzeug.utils import secure_filename

from database_tool import DatabaseApi
from model_tool import ModelApi

async_mode=None
app =Flask(__name__, static_folder='../frontend/build')
app.config['SECRET_KEY']='secret!'
thread_lock = Lock()
CORS(app)

g_check_list, g_manual_list, g_model_list = [], [], []
total_df = ''
db_control = DatabaseApi(db_path ='../database/test.db')
model_control = ModelApi()

#########
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
#########
# test code
# @app.route('/test_end', methods=['GET'])
# def test():
#     return "Test endpoint return!!!!"

###############
# upload part #
###############           
def excel_parser(excel_path):
    def refine_function(data):
        if data == str:
            temp = data.replace('\n',' ')
            while temp and not temp[0].isalnum():
                temp = temp[1:]
            return str(temp)
        else:
            return data
    df = pd.read_excel(excel_path)
    df.drop(['Unnamed: 3','Unnamed: 5','Unnamed: 6'], axis=1, inplace=True)
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = ['no','detail-E','detail-K','stand_sent']
    df['stand_sent'] = df['stand_sent'].apply(lambda x : refine_function(x))
    
    upload_no = list(df['no'])
    total_no = list(db_control.get_no_checkdetail()['no'])
    check_no =[]
    # print('total_no : ',total_no)
    for i in  df.iterrows():
        if i[1]['no'] not in total_no:
            value = (i[1]['no'], i[1]['detail-E'], i[1]['detail-K'], i[1]['stand_sent'])
            db_control.input_checkdetail(value)
        else:
            check_no.append(i[1]['no'])
    # print('duplic_check no :', check_no)
    df = db_control.get_sort_by_no_checkdetail(tuple(upload_no))
    return df

def pdf_parser(pdf_path, file_idx=1):
    idx = []
    sent = []
    page_num = []
    pdfFile= open(pdf_path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFile)
    pages=pdfReader.numPages
    print('page : ',pages)
    for num in range(1, pages):
        pageObj = pdfReader.getPage(num)
        text = pageObj.extract_text()
        matches = text.replace(' \n',' ')
        matches = re.split('\n',matches)
        print('num: ', num)
        for j in range(len(matches)):
            temp = matches[j]
            while temp and not temp[0].isalnum():
                temp = temp[1:]
            try:
                value = (file_idx, temp, num)
                print(value)
                db_control.input_manualdetail(value)
            except:
                temp = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', '', temp)
                value = (file_idx, temp, num)
                print(value)
                db_control.input_manualdetail(value)
            idx.append(file_idx)
            sent.append(temp)
            page_num.append(num)
            ## db 
            
    df = pd.DataFrame(data=zip(idx,sent,page_num), columns=['file_idx','sent','page_num'])
    return df

@app.route('/upload_func/', methods=['POST'])
def save_upload_file():
    global g_check_list, g_manual_list
    file = request.files['file']
    filename = secure_filename(file.filename)
    ext = filename.split('.')[-1]
    ## check files duplication at db
    save_path = '../tmp_doc'
    os.makedirs(save_path, exist_ok=True)
    file.save(f'{save_path}/{filename}')
    if ext =='pdf':
        db_filenames = db_control.read_db_table('Filename')
        if filename in list(db_filenames['name']):
            print('manual file duplication!! load DB file..')
            file_idx = db_filenames[db_filenames['name']==filename]['file_idx'][0]
            g_manual_list.append(db_control.get_manualdetail(file_idx))
        else:
            if len(db_filenames['file_idx'])==0:
                file_idx = 1
            else:
                file_idx = list(db_filenames['file_idx'])[-1]+1
            db_control.input_filename((filename, 'M'))
            parser_df = pdf_parser(f'{save_path}/{filename}')
            g_manual_list.append(parser_df)

    elif ext =='xlsx':
        parser_df = excel_parser(f'{save_path}/{filename}')
        g_check_list.append(parser_df)

    else:
        raise Exception('file extension is not "pdf","xlsx"')

    os.remove(f'{save_path}/{filename}')
    response = jsonify(True)
    return response

################
# predict part #
################  

def init_editdetail(m_idx, c_idx):
    for i in c_idx:
        values= (i, m_idx)
        db_control.input_editdetail(values)

def check_edit(m_idx, c_idx):
    edit_table = db_control.get_editdetail(m_idx, tuple(c_idx))
    if edit_table.shape[0]==0:
        init_editdetail(m_idx, c_idx)
        edit_table = db_control.get_editdetail(m_idx, tuple(c_idx))
    return edit_table

def merge_df(df_check, df_predict, df_edit):
    result_df = pd.merge(df_check, df_predict, on='total_idx', how='outer')
    result_df = pd.merge(result_df, df_edit, on='total_idx', how='outer')
    return result_df

@app.route('/run_predict_func/', methods=['POST'])
def run_predict():
    global g_check_list, g_manual_list, g_model_list, total_df
    # print('g_check_list', g_check_list)
    df_check = g_check_list[0]
    df_manual_list = g_manual_list
    edit_list = [check_edit(m_idx['file_idx'].iloc[0], list(df_check['total_idx'])) for m_idx in g_manual_list]
    df_predictdetail_list = [model_control.set_top3(df_check, df_manual) for df_manual in df_manual_list]
    ## concat checklist, maunal, edit
    df_concat = [merge_df(df_check, df_p, df_e) for df_p, df_e in zip(df_predictdetail_list, edit_list)]
    ## sending predict result to db
    for df_predictdetail in df_predictdetail_list:
        for i in df_predictdetail.iterrows():
            values = (i[1]['total_idx'],i[1]['file_idx'],i[1]['model_idx'],
            i[1]['sent_idx1'],i[1]['sent_idx2'],i[1]['sent_idx3'],
            i[1]['simility_score1'],i[1]['simility_score2'],i[1]['simility_score3'])
            db_control.input_predictdetail(values)

    # print('concat dataframe : /n')
    # for tmp in df_concat:
    #     print(tmp)
    total_df = df_concat
    return {'data' : [df.to_json() for df in df_concat]}

######
######



@app.route('/reset_func', methods=['GET'])
def reset_func():
    global g_check_list, g_manual_list, g_model_list, total_df
    # print('before g_check_list :', g_check_list)
    # print('before g_manual_list :', g_manual_list)
    # print('before g_model_list :', g_model_list)
    g_check_list, g_manual_list, g_model_list= [], [], []
    total_df = ''
    response = jsonify(True)
    print('after g_check_list :', g_check_list)
    print('after g_manual_list :', g_manual_list)
    print('after g_model_list :', g_model_list)
    return response

@app.route('/save_edit', methods=['POST'])
def save_edit():
    global g_check_list, g_manual_list, g_model_list
    file = request.files['file']
    ## save edit result

@app.route('/save_predict', methods=['POST'])
def save_predict():
    global g_check_list, g_manual_list, g_model_list
    output_path = '../export_files'
    os.makedirs(output_path, exist_ok='True')

    ## request file info
    file = request.files['file']


    df_save_result = pd.read_json(file)
    save_fn = datetime.now().isoformat().split('.')[0]
    df_save_result.to_excel(os.path.join(output_path, f'{save_fn}.xlsx'))


@app.route('/train_model', methods=['POST'])
def train_model():
    global g_check_list, g_manual_list, g_model_list, total_df
    # file = request.files['file']
    for df in total_df:
        train_df = df[['stand_sent','sent1','simility_score1']]
        model_control.fine_tuning(train_df)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug = True)