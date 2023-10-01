
# %%
from flask import request, Flask, jsonify
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import sqlite3
app = Flask(__name__)

app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing and Modeling')
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,
                 config=swagger_config)

df_abusive = pd.read_csv('abusive.csv', encoding='latin-1')

@swag_from("C:/Users/User/Documents/data science/Challenge/docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "Menyapa Hello World",
        'data': "Hello World"
    }
    
    response_data=jsonify(json_response)
    return response_data

@swag_from("C:/Users/User/Documents/data science/Challenge/docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])

def text_processing():
    
    text = request.form.get('text')
    
    
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': re.sub(r'[^a-zA-Z0-9]',' ',text),
    }
    
    
    response_data=jsonify(json_response)
    return response_data

@swag_from("C:/Users/User/Documents/data science/Challenge/docs/file_processing.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():
    global file, df, new_df, final_df, sql_database
    
    file = request.files.get('file')
    df = pd.read_csv(file, encoding='latin-1')
    
    json_response = {
        'status_code': 200,
        'description': "File berisi teks yang akan diproses",
        'data': "File berhasil diinput dan diproses"
    }
    # menghilangkan data yang duplikat
    df.drop_duplicates(inplace=True)
    
    # cleansing data menggunakan regex
    new_list = []
    for i in range(len(df)):
        cleaned_text_a = re.sub(r'[^a-zA-Z0-9]'," " ,df['Tweet'].iloc[i])
        cleaned_text_b = re.sub('RT',' ', cleaned_text_a)
        cleaned_text_c = re.sub('\\+n',' ', cleaned_text_b)
        cleaned_text_d = re.sub('rt',' ', cleaned_text_c)
        cleaned_text_e = re.sub('user',' ', cleaned_text_d)
        cleaned_text_f = re.sub('USER',' ', cleaned_text_e)
        cleaned_text_g = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+)|(URL))','', cleaned_text_f)
        cleaned_text_h = re.sub(':',' ', cleaned_text_g)
        cleaned_text_i = re.sub(';',' ', cleaned_text_h)
        cleaned_text_j = re.sub('\\+',' ', cleaned_text_i)
        cleaned_text_k = re.sub('  +',' ', cleaned_text_j)
        cleaned_text_l = re.sub('x..',' ', cleaned_text_k)
        cleaned_text_m = re.sub(' n ',' ', cleaned_text_l)
        new_list.append(cleaned_text_m)
       
    # masukkan proses cleansing data pada kolom Tweet
    new_df = df.copy()
    new_df['Tweet'] = new_list
    
    # membuat dataframe dengan menggabungkan kolom Tweet yang sudah dibersihkan dan sebelum dibersihkan dan menambahkan kolom number character dan number word 
    final_df = pd.concat([df['Tweet'],new_df['Tweet']],axis=1)
    final_df.columns = ['old','new']
    final_df['no_char_old'] = final_df['old'].apply(len)
    final_df['no_word_old'] = final_df['old'].apply(lambda x: len(x.split()))
    final_df['no_char_new'] = final_df['new'].apply(len)
    final_df['no_word_new'] = final_df['new'].apply(lambda x: len(x.split()))
    
    # buat fungsi untuk mengetahui berapa abusive word pada setiap baris
    def count_abusive(x):
        cleaned_tweet = x
        matched_list = []
        for i in range(len(df_abusive)):
            for j in x.split():
                word = df_abusive['ABUSIVE'].iloc[i]
                if word==j.lower():
                    matched_list.append(word)
        return len(matched_list)
    
    # masukkan fungsi tersebut kedalam kolom baru yang berisi jumlah abusive word pada tweet
    final_df['no_abusive'] = final_df['new'].apply(lambda x: count_abusive(x))
    
    # buat database menggunakan sqlite3
    conn = sqlite3.connect('test1.db')
    q_create_table = """
    create table if not exists final_df (old varchar(255), new varchar(255), no_char_old int, no_word_old int, no_char_new int, no_word_new int, no_abusive int);
    """
    conn.execute(q_create_table)
    conn.commit()
    
    # DO ITERATIONS TO INSERT DATA (EACH ROW) FROM FINAL DATAFRAME (POST_DF)
    for i in range(len(final_df)):
        old = final_df['old'].iloc[i]
        new = final_df['new'].iloc[i]
        no_char_old = int(final_df['no_char_old'].iloc[i])
        no_word_old = int(final_df['no_word_old'].iloc[i])
        no_char_new = int(final_df['no_char_new'].iloc[i])
        no_word_new = int(final_df['no_word_new'].iloc[i])
        no_abusive = int(final_df['no_abusive'].iloc[i])
    
        q_insertion = "insert into final_df (old, new, no_char_old, no_word_old, no_char_new, no_word_new, no_abusive) values (?,?,?,?,?,?,?)"
        conn.execute(q_insertion,(old,new,no_char_old,no_word_old,no_char_new,no_word_new,no_abusive))
        conn.commit()
        
    conn.close()
    
    plt.figure(figsize=(10,7))
    countplot = sns.countplot(data=final_df, x="no_abusive")
    for p in countplot.patches:
        countplot.annotate(format(p.get_height(), '.0f'), (p.get_x() + p.get_width() / 2., p.get_height()),  ha = 'center'
                            , va = 'center', xytext = (0, 10), textcoords = 'offset points')

    # %matplotlib inline
    # warnings.filterwarnings('ignore', category=FutureWarning)

    plt.title('Count of Estimated Number of Abusive Words')
    plt.xlabel('Estimated Number of Abusive Words')
    plt.savefig('new_countplot.jpeg')
    
    plt.figure(figsize=(20,4))
    boxplot = sns.boxplot(data=final_df, x="no_word_new")

    print()
    
    # VISUALIZE THE NUMBER OF WORDS USING BOXPLOT
    # %matplotlib inline
    # warnings.filterwarnings('ignore', category=FutureWarning)

    plt.title('Number of Words Boxplot (after tweet cleansing)')
    plt.xlabel('')
    plt.savefig('new_boxplot.jpeg')
    
    plt.figure(figsize=(20,4))
    boxplot_char = sns.boxplot(data=final_df, x="no_char_new")

    print()
    plt.title('Number of Character Boxplot (after tweet cleansing)')
    plt.xlabel('')
    plt.savefig('char_boxplot.jpeg')

    
    
   # OUTPUT THE RESULT IN JSON FORMAT
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': list(final_df['new'])
    }
    
    response_data = jsonify(json_response)
    return response_data

if __name__ == "__main__":
    app.run()