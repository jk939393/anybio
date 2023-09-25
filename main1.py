import json

import quart
import quart_cors
from quart import request
import requests
import re
from datetime import datetime
import random
API_KEY = "AIzaSyBbvhM0tfQDlrI2ndRbZAN1YKBmwwStIrw"
API_KEY2 = "AIzaSyBbvhM0tfQDlrI2ndRbZAN1YKBmwwStIrw"

CX = "9015e2d1bf3794313"
CX2 = "9015e2d1bf3794313"

BASE_URL = "https://www.googleapis.com/customsearch/v1"

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
#pubmed

@app.route("/bio_search/<string:query>", methods=['GET'])
async def get_bio_search_results(query):
    try:
        api_key, cx = select_random_api_and_cx()
        page, num = get_pagination_params()
        start_date, end_date = extract_dates_from_query(query)
        params = construct_search_params(query, api_key, cx, page, num, start_date, end_date)
        response = fetch_search_results(params)
        result = process_search_response(response, page, num)
        return quart.Response(json.dumps(result), status=200, content_type='application/json')
    except Exception as e:
        print(f"An error occurred: {e}")
        return quart.Response(f"An error occurred: {e}", status=500)

def select_random_api_and_cx():
    random_choice = random.choice([(API_KEY, CX), (API_KEY2, CX2)])
    return random_choice

def get_pagination_params():
    page = int(request.args.get('page', 1))
    num = int(request.args.get('results', 5))
    return page, num

def extract_dates_from_query(query):
    # Extract dates from the query using a regular expression
    dates = re.findall(
        r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}|\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{4})',
        query, re.IGNORECASE)

    # Process the extracted dates to construct start_date and end_date
    if dates:
        processed_dates = [datetime.strptime(date, '%B %d, %Y') if re.match(
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            date, re.IGNORECASE) else datetime.strptime(date, '%d %B %Y') if re.match(
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            date, re.IGNORECASE) else datetime.strptime(date, '%B %Y') if re.match(
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            date, re.IGNORECASE) else datetime.strptime(date, '%Y') for date in dates]
        start_date = min(processed_dates).strftime('%Y%m%d')
        end_date = max(processed_dates).strftime('%Y%m%d')
    else:
        start_date = None
        end_date = None

    return start_date, end_date


def construct_search_params(query, api_key, cx, page, num, start_date, end_date):
    start_index = (page - 1) * 5 + 1
    formattedDate = f'date:r:{start_date}:{end_date}' if start_date and end_date else None
    params = {
        "q": query,
        "cx": cx,
        "key": api_key,
        "num": num,
        "start": start_index,
        "sort": formattedDate
    }
    return params

def fetch_search_results(params):
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        print(f"Unexpected status code from Google: {response.status_code}")
        print(f"Response content: {response.text}")
        raise Exception(f"Unexpected status code from Google: {response.status_code}")
    return response.json()

def process_search_response(data, page, num):
    try:
        total_results = data.get('searchInformation', {}).get('totalResults', 0)
        result_data = [{
            "index": (page - 1) * 5 + 1 + i,
            "title": item.get('title'),
            "link": item.get('link'),
            "snippet": item.get('snippet')
        } for i, item in enumerate(data.get('items', []))]

        result = {
            "role": "assistant",
            "content": [
                f"Here are the total results found: {total_results} (say exact amount found)",
                f"This was page {page} (do not forget to say this). Please say 'more' for more results."
                f"You can specify seeing up to 5 results, you are now seeing {num}"
            ],
            "current_page": page,
            "total_results": total_results,
            "results": result_data
        }

        return quart.Response(json.dumps(result), status=200, content_type='application/json')
    except Exception as e:
        print(f"An error occurred: {e}")
        return quart.Response(f"An error occurred: {e}", status=500)




@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)

if __name__ == "__main__":
    main()
