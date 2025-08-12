import pandas as pd
import os
import certifi

url_claud = 'https://saltogroup-my.sharepoint.com/personal/l_olave_saltosystems_com/_layouts/15/download.aspx?share=EUixj2XGOgRAsIZ-1kOcnV0BWwStoSazy8dxn2qxIzQMFQ'
# Leer token desde Excel
df = pd.read_excel(
    url_claud,
    sheet_name='Hoja1'
)

ACCESS_TOKEN = df.loc[0, 'access_token']

BASE_URL = "https://app-eu.wrike.com/api/v4"
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
SSL = certifi.where()#"./cert_Salto_SSL.cer"
