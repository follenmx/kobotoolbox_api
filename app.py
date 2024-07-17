from dotenv import load_dotenv
from io import StringIO
import os
import requests
import csv
import pandas as pd

load_dotenv()

form_id = os.getenv('FORM_ID')
settings_id = os.getenv('SETTINGS_ID')
api_token = os.getenv('API_TOKEN')
url = f'https://eu.kobotoolbox.org/api/v2/assets/{form_id}/export-settings/{settings_id}/data.csv'

def get_data(url: str, token: str) -> pd.DataFrame:
    """
    Fetches data from the specified URL using the provided token for authorization and returns it as a pandas DataFrame.

    Parameters:
    url (str): The URL from which to fetch the data.
    token (str): The authorization token to be included in the request header.

    Returns:
    pd.DataFrame: A DataFrame containing the data fetched from the URL.
    """
    headers = {
        'Authorization': f'Token {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"There is a mistake, the status code is {response.status_code}")
    decoded_content = response.content.decode('utf-8')
    csv_data = StringIO(decoded_content)
    df_csv = pd.read_csv(csv_data, delimiter=';')
    return df_csv

df = get_data(url, 234)

