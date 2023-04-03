import os, sys ,glob
import pandas as pd
import numpy as np

from sentence_transformers import SentenceTransformer, util

# inputs =[
#     'Inert gas (oxygen free nitrogen) should be used when you checking for leaks, cleaning or repairs of pipes etc. If you are using combustible gases including oxygen, appliance may have the risk of fires and explosions.',
#     'Prior to recharging the system it shall be pressure tested with oxygen free nitrogen (OFN).',
#     'Oxygen free nitrogen (OFN) shall be purged through the system both before and during the brazing process.',
#     "'Use non-flammable gas (nitrogen) to CHECK for leak and to purge air.",
#     "Maintain a clearance of at least 10 cm from the right and left sides of the indoor unit."
# ]

# targets = [
#     "Inert gas (oxygen free nitrogen) should be used when you checking for leaks, cleaning or repairs of pipes etc. If you are using combustible gases including oxygen, appliance may have the risk of fires and explosions.",
#     "Prior to recharging the system it shall be pressure tested with oxygen free nitrogen (OFN).",
#     "Oxygen free nitrogen (OFN) shall be purged through the system both before and during the brazing process.",
#     "Use non-flammable gas (nitrogen) to CHECK for leak and to purge air.",
#     "Maintain a clearance of at least 10 cm from the right and left sides of the indoor unit."
# ]

# df = pd.DataFrame(zip(inputs, targets), columns=['inputs','targets'])

MODEL_LIST=[
    'bert-base-nli-mean-tokens',
    'all-MiniLM-L6-v2',
    'paraphrase-MiniLM-L6-v2',
    'paraphrase-multilingual-MiniLM-L12-v2',
    'all-mpnet-base-v2',
    'multi-qa-mpnet-base-dot-v1',
    'all-MiniLM-L12-v2',
    'paraphrase-mpnet-base-v2',
    'paraphrase-MiniLM-L12-v2',
    'LaBSE',
    'paraphrase-multilingual-mpnet-base-v2'
    ]

class ModelApi():
    def __init__(self, m_list=None):
        if m_list is None:
            self.model_list = MODEL_LIST
        else:
            if isinstance(m_list, list):
                self.model_list = m_list
            else:
                self.model_list= [m_list]
        self.models = [self.load_model(m_name) for m_name in self.model_list]

    def load_model(self, model_name):
        model = SentenceTransformer(model_name)
        return model

    def set_embedding(self, check_df, manual_df, model_num=None):
        if model_num is None:
            model_num = 1
        self.model_idx = model_num
        model = self.models[self.model_idx]
        self.em_inputs =  model.encode(check_df['stand_sent'])
        self.em_tartget = model.encode(manual_df['sent'])

    def set_top3(self, check_df, manual_df):
        self.set_embedding(check_df, manual_df)
        dot_score = util.dot_score(self.em_tartget, self.em_inputs)
        result_df = pd.DataFrame(data=dot_score)
        total_list = check_df['total_idx']
        manual_idx = manual_df['file_idx'][0]
        file_idx = [manual_idx for _ in range(result_df.shape[1])]
        model_idx = [self.model_idx for _ in range(result_df.shape[1])]
        sent_idx1 = []
        sent_idx2 = []
        sent_idx3 = []
        sim_score1 =[]
        sim_score2 =[]
        sim_score3 =[]
        for i in range(result_df.shape[1]): 
            # checklist sentence iteration
            df_sorted = result_df[i].sort_values(ascending=False)
            sent_idx1.append(manual_df['sent'].iloc[df_sorted.index[0]])
            sent_idx2.append(manual_df['sent'].iloc[df_sorted.index[1]])
            sent_idx3.append(manual_df['sent'].iloc[df_sorted.index[2]])
            sim_score1.append(round(float(df_sorted[df_sorted.index[0]]),2))
            sim_score2.append(round(float(df_sorted[df_sorted.index[1]]),2))
            sim_score3.append(round(float(df_sorted[df_sorted.index[2]]),2))
        send_db = pd.DataFrame(data=zip(
            total_list, file_idx, model_idx, 
            sent_idx1, sent_idx2, sent_idx3, 
            sim_score1, sim_score2, sim_score3
        ), columns=['total_idx', 'file_idx', 'model_idx', 
            'sent_idx1', 'sent_idx2', 'sent_idx3', 
            'simility_score1', 'simility_score2', 'simility_score3'])
        return send_db

    def fine_tuning(self, df):
        
        pass


# m_api = ModelApi()
