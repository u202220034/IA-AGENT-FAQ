
# prepare_hana.py  (ejecútalo desde BAS)
import os
import pandas as pd
import hana_ml.dataframe as hd

HANA_ADDRESS  = os.getenv("SAP_HANA_CLOUD_ADDRESS", "")
HANA_PORT     = int(os.getenv("SAP_HANA_CLOUD_PORT", "443"))
HANA_USER     = os.getenv("SAP_HANA_CLOUD_USER",  "")
HANA_PASSWORD = os.getenv("SAP_HANA_CLOUD_PASSWORD", "")

conn = hd.ConnectionContext(address=HANA_ADDRESS, port=HANA_PORT, user=HANA_USER, password=HANA_PASSWORD)

# 1) Lee Excel
df_q = pd.read_excel("./data/FAQ_ASSISTANT_QUESTIONS.xlsx")  # AID, QID, QUESTION
df_a = pd.read_excel("./data/FAQ_ASSISTANT_ANSWERS.xlsx")    # AID, ANSWER

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
