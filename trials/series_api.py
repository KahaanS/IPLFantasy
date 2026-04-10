import requests
import json
import sys
sys.path.append('../')
from helpers.api_helpers import load_config_yaml

config = load_config_yaml('../config.yaml')
apikey = str(config.get('API_KEY'))

id="87c62aac-bc3c-4738-ab93-19da0690488f"
response = requests.get("https://api.cricapi.com/v1/series_info?apikey="+apikey+"&offset=0&id="+id)
def myobj(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    with open("seriesinfo.json", "w") as f:
        f.write(text)
    data = json.loads(text)['data']['info']
    print("----------------------------Series Info -----------------")
    print(" Name - "+data['name']+" \n "+"End Date -   "+data['enddate']+" \n ")    
    print(" ODI - "+ str(data['odi']) +" Matches - "+ str(data['matches']) +" Test - "+ str(data['test']) )    

myobj(response.json())