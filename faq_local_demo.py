import os, json
from flask import Flask, request, jsonify
from gen_ai_hub.proxy.native.openai import chat


app = Flask(__name__)
# Port number is required to fetch from env variable
# http://docs.cloudfoundry.org/devguide/deploy-apps/environment-variable.html#PORT
cf_port = os.getenv("PORT")

# Credentials for SAP AI Core need to be set as environment variables in the manifest.yml file
# AICORE_AUTH_URL
# AICORE_BASE_URL
# AICORE_CLIENT_ID
# AICORE_CLIENT_SECRET
# AICORE_RESOURCE_GROUP

# Credentials for SAP HANA Cloud, hardcoded for testing
SAP_HANA_CLOUD_ADDRESS  = ""
SAP_HANA_CLOUD_PORT     = 443
SAP_HANA_CLOUD_USER     = ""
SAP_HANA_CLOUD_PASSWORD = ""
AI_CORE_MODEL_NAME      = "mistralai--mistral-large-instruct"

# Connect to SAP HANA Cloud
import hana_ml.dataframe as dataframe
conn = dataframe.ConnectionContext(
                                   address  = SAP_HANA_CLOUD_ADDRESS,
                                   port     = SAP_HANA_CLOUD_PORT,
                                   user     = SAP_HANA_CLOUD_USER,
                                   password = SAP_HANA_CLOUD_PASSWORD,
                                  )


@app.route("/", methods=["POST"])
def faq():
    payload = request.get_json(silent=True)
    if not payload or "user_request" not in payload:
        return jsonify({"error": "user_request is required"}), 400

    user_question = payload["user_request"]

    # --- embeddings ---
    user_question_sqlcompliant = user_question.replace("'", "''")
    sql = f"""
        SELECT VECTOR_EMBEDDING(
            '{user_question_sqlcompliant}',
            'QUERY',
            'SAP_NEB.20240715'
        ) AS EMBEDDEDQUESTION FROM DUMMY;
    """
    user_question_embedding_str = conn.sql(sql).head(1).collect().iloc[0, 0]

    sql = f"""
        SELECT TOP 20 "AID", "QID", "QUESTION",
        COSINE_SIMILARITY("QUESTION_VECTOR",
        TO_REAL_VECTOR('{user_question_embedding_str}')) AS SIMILARITY
        FROM CHATBOT_FAQ_QUESTIONS
        ORDER BY SIMILARITY DESC
    """
    df_data = (
        conn.sql(sql)
        .select("AID", "QID", "QUESTION")
        .head(10)
        .collect()
    )

    if df_data.empty:
        return jsonify({"faq_response": "No matching FAQ found"})

    

    df_data["ROWID"] = df_data["AID"].astype(str) + "-" + df_data["QID"].astype(str)
    candidates_str = df_data[["ROWID", "QUESTION"]].to_string(index=False)

    llm_prompt = f"""
Task: which of the following candidate questions is closest?
{user_question}
Only return the ID.

Candidates:
{candidates_str}
"""

    response = chat.completions.create(
        model_name=AI_CORE_MODEL_NAME,
        messages=[{"role": "user", "content": llm_prompt}],
        temperature=0
    )

    llm_response = response.choices[0].message.content.strip()

    if llm_response == "NONE":
        return jsonify({"faq_response": "No matching FAQ found"})

    aid, qid = llm_response.split("-")

    matching_answer = (
        conn.table("CHATBOT_FAQ_ANSWERS")
        .filter(f'"AID" = \'{aid}\'')
        .select("ANSWER")
        .head(1)
        .collect()
        .iloc[0, 0]
    )

    if matching_answer is None or matching_answer == "":
        return jsonify({"faq_response": "No answer found for the matched FAQ"})

    final_prompt = f"""
Answer the question using only the context.
Question: {user_question}
Context: {matching_answer}
"""

    response = chat.completions.create(
        model_name=AI_CORE_MODEL_NAME,
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0
    )

    return jsonify({
        "faq_response": response.choices[0].message.content.strip()
    })



if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(cf_port or 8080),
        debug=False
    )

