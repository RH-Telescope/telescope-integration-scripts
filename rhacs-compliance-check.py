import sys,socket
import requests
import json
import math
import psycopg2
from config import config

conn = None
params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()

# Get relevant db objects
telescope_query = "SELECT * from integrations WHERE integration_name = 'RHACS Compliance Score'"
cur.execute(telescope_query)
row = cur.fetchone()

INTEGRATION_ID = row[0]
CAPABILITY_ID = row[1]
ACS_ENDPOINT = row[2]
ACS_TOKEN = row[5]
SUCCESS_CRITERIA = int(row[6])

success = 0
failure = 0
flag_id = 1
headers = {'Authorization': "Bearer {}".format(ACS_TOKEN)}
jsonResponse = requests.get(ACS_ENDPOINT, headers=headers).json()

for results in jsonResponse['results']['clusterResults']['controlResults']:
    complianceStatus = jsonResponse['results']['clusterResults']['controlResults'][results]['overallState']
    if complianceStatus == "COMPLIANCE_STATE_SUCCESS":
        success += 1
    if complianceStatus == "COMPLIANCE_STATE_FAILURE":
        failure += 1
total = success + failure 
score = (success / total) * 100
#print(math.ceil(score))

if score >= SUCCESS_CRITERIA:
	flag_id = 2

## Update the capability table with the new flag_id (1 = red, 2 = green)
updateQuery = "UPDATE capability set flag_id = '" + str(flag_id) + "' WHERE id = '" + str(CAPABILITY_ID) + "'"
cur.execute(updateQuery)
conn.commit()

cur.close()
