import requests
paylod = {'user_request': 'Who is the boss at SAP?'}
url = 'https://faq.cfapps.us10-001.hana.ondemand.com'
headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
r = requests.get(url, json=paylod, headers=headers, verify=False)
response = r.json()
faq_response = response['faq_response'] # final answer
faq_response_log = response['faq_response_log'] # log of the individual steps