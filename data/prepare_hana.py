# prepare_hana.py  (ejecútalo desde BAS)
import os
import pandas as pd
import hana_ml.dataframe as hd
from datetime import datetime

HANA_ADDRESS  = os.getenv("SAP_HANA_CLOUD_ADDRESS", "")
HANA_PORT     = int(os.getenv("SAP_HANA_CLOUD_PORT", "443"))
HANA_USER     = os.getenv("SAP_HANA_CLOUD_USER",  "")
HANA_PASSWORD = os.getenv("SAP_HANA_CLOUD_PASSWORD", "")

# Conexión a HANA
conn = hd.ConnectionContext(address=HANA_ADDRESS, port=HANA_PORT, user=HANA_USER, password=HANA_PASSWORD)

# 1) Lee Excel
df_q = pd.read_excel("./data/FAQ_ASSISTANT_QUESTIONS.xlsx")  
df_a = pd.read_excel("./data/FAQ_ASSISTANT_ANSWERS.xlsx")    

df_q['STATUS'] = 'ACTIVE'
df_q['CREATED_AT'] = pd.Timestamp.now()
df_q['CREATED_BY'] = 'INITIAL_LOAD' 
# Nota: QUESTION_VECTOR se creará como NULL automáticamente, y lo llenarás luego con tu query SQL.

# ==========================================

# 2) Inserta (append) en tablas **ya creadas** (NO recrea)
hd.create_dataframe_from_pandas(
    conn, df_q,
    table_name='CHATBOT_FAQ_QUESTIONS', schema='DBADMIN',
    force=False, replace=False, append=True  # << clave
)

hd.create_dataframe_from_pandas(
    conn, df_a,
    table_name='CHATBOT_FAQ_ANSWERS', schema='DBADMIN',
    force=False, replace=False, append=True  # << clave
)

print("Insertados registros en DBADMIN.CHATBOT_FAQ_QUESTIONS / DBADMIN.CHATBOT_FAQ_ANSWERS")
