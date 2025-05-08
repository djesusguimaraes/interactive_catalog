import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime, timedelta
import pyodbc
import numpy as np

# Configurações
ORGANIZATION = "stgcs-br02-innopex"
PROJECT = "Innovation%20Labs"  # Codificado para URL
REPO = "interactive-catalog"
PAT = "7QFaXJvjLEJJGmjBof7BZt2ITnvK4HMcTZg8tqAobSA6HU0XFX1iJQQJ99BCACAAAAABgmZbAAASAZDOXZFH"

#develop ou main
BRANCH = "develop"

# URL da API para buscar os itens do repositório
URL = f"https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/git/repositories/{REPO}/items?recursionLevel=Full&version={BRANCH}&api-version=7.1-preview.1"

# Autenticação
HEADERS = {"Content-Type": "application/json"}
AUTH = ("", PAT)

print("Processando repositório...")
# Requisição para obter os arquivos e pastas
response = requests.get(URL, headers=HEADERS, auth=AUTH)

if response.status_code == 200:
    items = response.json()["value"]

## Pegar tudo dentro de pastas_src, todas as subcategorys e todas as familys
pastas_src = []
lista_subcategorys = []
lista_familys = []

for item in items:
    if item.get("isFolder") == True:
        path = item["path"].strip("/")
        parts = path.split("/")

        if parts[0] == "src" and len(parts) > 1:
            pastas_src.append(parts)

        try:
            lista_familys.append(parts[1])
        except:
            continue
        try:
            lista_subcategorys.append(parts[2])
        except:
            continue

lista_familys = list(set(lista_familys))
lista_subcategorys = list(set(lista_subcategorys))

#Ver quando devemos manter uma pasta por conta da family
lista_manter_family = []
for family in lista_familys:
    count = 0
    for pastas in pastas_src:
        if family in pastas:
            count += 1
        
    if count == 1:
        lista_manter_family.append(family)

#Ver quando devemos manter uma pasta por conta da subcategory
lista_manter_subcategory = []
for subcategory in lista_subcategorys:
    count = 0
    for pastas in pastas_src:
        if subcategory in pastas:
            count += 1
        
    if count == 1:
        lista_manter_subcategory.append(subcategory)

#Filtrar pastas finais
pastas_finais = []
for pasta in pastas_src:

    family = pasta[1]
    try:
        subcategory = pasta[2]
    except:
        subcategory = None
    
    if "fragments" in pasta: #não queremos pegar os index.html dentro de fragments
        continue #aqui vai o código par identificar e montar a base de fragments
    else:
        if (pasta[-1].isdigit()) or (family in lista_manter_family) or (subcategory in lista_manter_subcategory):
            pastas_finais.append("/" + "/".join(pasta) + "/index.html")
    
#Coleta links do index.html
lista_urls = []
for dir in pastas_finais:
    for item in items:

        if item.get("path") == dir:
            lista_urls.append(item.get("url"))

#coleta produtos dentro do index.html
lista_products = []
lista_is_sku = []
for url in lista_urls:
    response = requests.get(url, headers=HEADERS, auth=AUTH)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        products = []
        is_sku = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if href.startswith("javascript:addToCartBySku"):
                products.append(href)
                is_sku.append(1)
            else:
                if href.startswith("javascript:addToCartByText"):
                    products.append(href)
                    is_sku.append(0)
                
                elif href.startswith("javascript:addToCartByVariations"):
                    href = re.findall(r"\((.*?)\)", href)
                    product_list = href[0].replace("[", "").replace("]", "").split(",")
                    for product in product_list:
                        products.append(product)
                        if re.findall(r'\d+\.\d+', product): # se bate com a regex de sku
                            is_sku.append(1)
                        else:
                            is_sku.append(0)

        products_formatados = []

        for produto in products:
            match = re.findall(r"\((.*?)\)", produto)
            if match:
                products_formatados.append(match[0].replace("'", ""))
            else:
                products_formatados.append(produto.replace("'", ""))


        lista_products.append(products_formatados)
        lista_is_sku.append(is_sku)

#formata colunas do dataframe
family_df = []
subcategory_df = []
pagina_df = []
for dir in pastas_finais:
    dir = dir.replace("/src/", "").replace("/index.html", "").split("/")

    if len(dir) == 1:
        family_df.append(dir[0])
        subcategory_df.append(None)
        pagina_df.append(None)
    elif len(dir) == 2:
        family_df.append(dir[0])
        subcategory_df.append(dir[1])
        pagina_df.append(None)
    elif len(dir) == 3:
        family_df.append(dir[0])
        subcategory_df.append(dir[1])
        pagina_df.append(dir[2])

#Cria DataFrame
df_pages = pd.DataFrame({
    "family": family_df,
    "subcategory":subcategory_df,
    "max_page_number": pagina_df,
    "product":lista_products,
    "is_sku": lista_is_sku
})

#Formata o Dataframe
df_pages["link"] = df_pages.apply(lambda row: 
                          f"http://{BRANCH}-{REPO}"+ ".s3-website-us-east-1.amazonaws.com/src/" + row["family"] + "/" + row["subcategory"] + "/"
                          if row["subcategory"] #and not row['subcategory'].isnumeric()
                          else 
                          f"http://{BRANCH}-{REPO}"+ ".s3-website-us-east-1.amazonaws.com/src/" + row["family"] + "/", axis = 1)

df_products = df_pages[["link", "product", "max_page_number", "is_sku"]]
df_products = df_products.copy()
df_products.rename(columns={"max_page_number": "page"}, inplace=True)
df_products = df_products.explode(['is_sku', 'product']).reset_index(drop=True)
df_products = df_products.where(pd.notna(df_products), None)
df_products["product"] = df_products["product"].str.replace(r'^\s+|\s+$', '', regex=True)

df_pages = df_pages[["family", "subcategory", "max_page_number", "link"]]
df_pages = df_pages.copy()
df_pages.loc[:, "image"] = None
df_pages = df_pages.sort_values("max_page_number", ascending=False).drop_duplicates(subset=["family", "subcategory"], keep="first").sort_values(["family", "subcategory"])

df_pages = df_pages.reset_index(drop = True)
df_products = df_products.reset_index(drop = True)

#==== Essa parte de baixo é apenas um fix para corrigir a possibilidade de não existir subcategoria mas existir pages
#==== foi mais fácil fazer esse fix que remodelar o código acima
def somente_numeros(s):
    return bool(re.fullmatch(r'\d+', s))

families_to_fix = []
for index, row in df_pages.iterrows():
    if row["subcategory"] != None:
        flag_numeros = somente_numeros(row["subcategory"]) #checa se subcategoria eh apenas um numero
        if flag_numeros == True:
            families_to_fix.append(row["family"]) #Salva a familia para corrigir na tabela products
            df_pages.at[index, "max_page_number"] = row["subcategory"] #substitui o numero da pagina pela subcategoria
            df_pages.at[index, "subcategory"] = None #apaga subcategoria

df_pages = df_pages.groupby(["family", "subcategory", "link", "image"], dropna=False)\
    .agg({"max_page_number": "max"})\
    .sort_values(["family", "subcategory"])\
    .reset_index() #Agrega tudo para pegar somente a maior pagina
df_pages = df_pages[["family", "subcategory", "max_page_number", "link", "image"]] ##reordena colunas
df_pages = df_pages.astype(str).replace("nan", None) #garante str nas colunas

families_to_fix = list(set(families_to_fix)) # dropa duplicados das familias para corrigir tabela products

for family in families_to_fix:
    string_split = f"src/{family}/"
    mask_products = df_products["link"].str.contains(string_split, na=False) #verifica quando link possui uma familia que precisa ser corrigida
    df_products.loc[mask_products, "page"] = df_products.loc[mask_products, "link"]\
        .str.split(string_split)\
        .str[1].str.replace("/", "", regex = False) # preenche o numero da pagina

#Corrigir o link
df_products['link'] = df_products['link'].apply(lambda x: re.sub(r'/(\d+)/?$', '/', x))
df_pages['link'] = df_pages['link'].apply(lambda x: re.sub(r'/(\d+)/?$', '/', x))

df_pages = df_pages.groupby(["family", "subcategory", "link", "image"], dropna=False)\
    .agg({"max_page_number": "max"})\
    .sort_values(["family", "subcategory"])\
    .reset_index() #Agrega tudo para pegar somente a maior pagina
df_pages = df_pages.astype(str).replace("nan", None) #garante str nas colunas
df_pages = df_pages[["family", "subcategory", "max_page_number", "link", "image"]]

print("Registros em interactive_catalog_pages: ", len(df_pages))
print("Registros em interactive_catalog_products: ", len(df_products))

#=====================================================SALVA BASES==========================================================================

print("Salvando...")

#Credenciais connect
server = 'datalake-sql-smilink.database.windows.net'

#Dependendo de qual branch foi lida, salva no banco de homolog ou produção
if BRANCH == "develop":
    database = 'sap-alteryx-hom'
elif BRANCH == "main":
    database = "sap-alteryx"

username = 'adminSmilink'
password = 'Smilinkinha@2023'
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes'

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

#Salva base pages
table_name = "interactive_catalog_page"

# Delete records from the table
cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
conn.commit()

# Recreate the table with all columns as VARCHAR(MAX)
columns = ", ".join([f"{col} VARCHAR(MAX)" for col in df_pages.columns])
cursor.execute(f"CREATE TABLE {table_name} ({columns})")
conn.commit()

# Insert DataFrame into the table
for _, row in df_pages.iterrows():
    placeholders = ",  ".join("?" * len(row))
    query = f"INSERT INTO {table_name} VALUES ({placeholders})"
    cursor.execute(query, *row)
conn.commit()
#conn.close()

#salva base produtos
table_name = "interactive_catalog_product"

# Delete records from the table
cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
conn.commit()

# Recreate the table with all columns as VARCHAR(MAX)
columns = ", ".join([f"{col} VARCHAR(MAX)" if col not in ['page', 'is_sku'] else f"{col} INT" for col in df_products.columns])
cursor.execute(f"CREATE TABLE {table_name} ({columns})")
conn.commit()

# Insert DataFrame into the table
for _, row in df_products.iterrows():
    placeholders = ",  ".join("?" * len(row))
    query = f"INSERT INTO {table_name} VALUES ({placeholders})"
    cursor.execute(query, *row)
conn.commit()
conn.close()