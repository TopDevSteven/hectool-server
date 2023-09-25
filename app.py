from fastapi import FastAPI, Request, HTTPException
from starlette.responses import RedirectResponse
import hashlib
import httpx
import hmac as HM
from urllib.parse import urlencode
import ast
import re
from langchain import OpenAI, SQLDatabase , SQLDatabaseChain
from langchain.chat_models import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import os
import math
import sqlite3
from sqlite_utils import Database
from pydantic import BaseModel
from googletrans import Translator
from fastapi.responses import FileResponse
from datetime import datetime

translator = Translator()

from operate import greeting

load_dotenv()

#from .env
redirect_uri = os.getenv("Redirect_URL")
api_key = os.getenv("API_KEY")
shared_secret = os.getenv("SECRET_KEY")
access_token = os.getenv("ACCESS_TOKEN")
store_name = os.getenv("SHOPIFY_STORE_NAME")
openai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
token_limit = 3000
page_limit = 10
store_endpoint = f"https://{store_name}.myshopify.com/admin/products.json?limit={page_limit}"

# Define SQLDatabaseChain

llm = ChatOpenAI(model_name='gpt-3.5-turbo', openai_api_key=openai_key, temperature=0.3)

current_path = os.path.dirname(__file__)
dburi = os.path.join('sqlite:///' + current_path,
                     "db", "product.db")
db = SQLDatabase.from_uri(dburi)
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_direct = True, return_intermediate_steps=True)
chat_db = Database("./db/chathistory.db")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    sessionid: str
    role: str
    content: str


greetings = ['hello', 'hi', 'good morning', 'good afternoon', 'hello?', 'hi?']

@app.get("/hello/")
def read_root():
    return "Hello World"

@app.get("/test/")
def test():
    conn = sqlite3.connect(r"./db/product.db")
    cursor = conn.cursor()
    name = "Clamping Heads"
    shape = "Round"
    type = "Type 32L"
    item = None
    bore = "L(smooth)"
    d_min = 4.0
    d_max = 32.0
    vendor = "DT GROUP"
    size = None
    id = 5
    cursor.execute("SELECT * FROM products WHERE name=? AND form=? AND ref_no IS NULL AND shape=? AND bore=? AND diameter_min=? AND diameter_max=? AND vendor=? AND size is NULL", (name, type, shape, bore, d_min, d_max, vendor))
    # cursor.execute("SELECT * FROM products WHERE id = ?", (id,))
    num = cursor.fetchall()
    print(len(num))
    for list in num:
        print(list)
    return "Suc"

@app.get("/install/")
async def install(shop: str):
    scopes = "read_orders,read_products"
    install_url = f"https://{shop}.myshopify.com/admin/oauth/authorize?client_id={api_key}&scope={scopes}&redirect_uri={redirect_uri}"
    return RedirectResponse(url=install_url)


@app.get("/generate/")
async def generate(request: Request):
    query_params = request.query_params
    hmac = query_params['hmac']
    code  = query_params['code']
    shop  = query_params['shop']
    
    print(query_params)
    param_name_to_remove = "hmac"
    filtered_params = {key: value for key, value in query_params.items() if key != param_name_to_remove}
    sorted_params = dict(sorted(filtered_params.items()))
    print(sorted_params)  
    
    computed_hmac = HM.new(shared_secret.encode(), urlencode(sorted_params).encode(), hashlib.sha256).hexdigest()
    print(computed_hmac)
    
    if HM.compare_digest(hmac, computed_hmac):
        query = {
            "client_id": api_key,
            "client_secret": shared_secret,
            "code": code,
        }
        access_token_url = f"https://{shop}/admin/oauth/access_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(access_token_url, data=query)   
        result = await response.json()
        print(result)
        
        access_token = result["access_token"]
        return access_token
    
    else:
        raise HTTPException(status_code=401, detail="HMAC verification failed")
    

@app.get("/new-orders/")
async def get_orders():
    
    conn = sqlite3.connect(r"./db/product.db")
    cursor = conn.cursor()
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }

    async def insert(rlt):
        for tool in rlt:
            if "Kit" in tool['title']:
                pass
            
            elif "Clamping" in tool['title']:
                title = tool['title']
                link = "https://www.hectool.com/" + tool['handle']
                name = tool['title'].split(" - ")[0]
                type = tool['title'].split(" - ")[1]
                item = None
                d_min = float(tool['options'][0]['values'][0])
                d_max = float(tool['options'][0]['values'][len(tool['options'][0]['values']) - 1])
                if len(tool['options'][0]['values']) > 1:
                    d_step = float(tool['options'][0]['values'][1]) - float(tool['options'][0]['values'][0])
                else: d_step = None
                shape = tool['title'].split(" - ")[2]
                bore = tool['title'].split(" - ")[3]
                vendor = tool['vendor']
                size = None
                cursor.execute("SELECT * FROM products WHERE name=? AND form=? AND shape=? AND bore=? AND diameter_min=? AND diameter_max=? AND vendor=?", (name, type, shape, bore, d_min, d_max, vendor))
                num = cursor.fetchall()
                print(len(num))
                if(len(num) > 0): pass
                else:
                    cursor.execute("INSERT INTO products (name, form, ref_no, shape, bore, diameter_min, diameter_max, diameter_step, vendor, size, link, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, type, item, shape, bore, d_min, d_max, d_step, vendor, size, link, title))
                    conn.commit()
                
            elif "Collets" in tool['title']:
                title = tool['title']
                link = "https://www.hectool.com/" + tool['handle']
                name = tool['title'].split(" - ")[0]
                type = tool['title'].split(" - ")[1]
                item = tool['title'].split(" - ")[2]
                shape = tool['title'].split(" - ")[3]
                bore = tool['title'].split(" - ")[4]
                vendor = tool['vendor']
                if tool['options'][0]['values'][0] == "-":
                    d_min = None
                    d_max = None
                    d_step = None
                else:
                    d_min = float(tool['options'][0]['values'][0])
                    d_max = float(tool['options'][0]['values'][len(tool['options'][0]['values']) - 1])
                    if len(tool['options'][0]['values']) > 1:
                        d_step = float(tool['options'][0]['values'][1]) - float(tool['options'][0]['values'][0])
                    else: d_step = None
                size = None
                cursor.execute("SELECT * FROM products WHERE name=? AND form=? AND ref_no=? AND shape=? AND bore=? AND vendor=?", (name, type, item, shape, bore, vendor))
                num = cursor.fetchall()
                if(len(num) > 0): pass
                else:
                    cursor.execute("INSERT INTO products (name, form, ref_no, shape, bore, diameter_min, diameter_max, diameter_step, vendor, size, link, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, type, item, shape, bore, d_min, d_max, d_step, vendor, size, link, title))                
                    conn.commit()
                
            elif "Chuck" in tool['title']:
                print("THis is Chuck")
                title = tool['title']
                link = "https://www.hectool.com/" + tool['handle']
                name = tool['title'].split(" Chuck ")[0] + "Chuck"
                vendor = tool['title'].split(" Chuck ")[1].split(" ")[0]
                size = tool['title'].split(" Chuck ")[1].split(" ")[1]
                item = tool['title'].split(" Chuck ")[1].split(" ")[2]
                bore = None
                shape = None
                d_min = float(tool['options'][0]['values'][0])
                d_max = float(tool['options'][0]['values'][len(tool['options'][0]['values']) - 1])
                if len(tool['options'][0]['values']) > 1:
                    d_step = float(tool['options'][0]['values'][1]) - float(tool['options'][0]['values'][0])
                else: d_step = None
                type = None
                cursor.execute("SELECT * FROM products WHERE name=? AND ref_no=? AND diameter_min=? AND diameter_max=? AND vendor=? AND size=?", (name,item, d_min, d_max, vendor, size))
                num = cursor.fetchall()
                if(len(num) > 0): pass
                else:
                    cursor.execute("INSERT INTO products (name, form, ref_no, shape, bore, diameter_min, diameter_max, diameter_step, vendor, size, link, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, type, item, shape, bore, d_min, d_max, d_step, vendor, size, link, title))
                    conn.commit()
                            
            else:
                pass
            
        return "success"
    counturl = "https://hectool-app-development.myshopify.com/admin/products/count.json"
    async with httpx.AsyncClient() as client:
            response = await client.get(counturl, headers=headers)
    count = response.json()['count']
    count = math.ceil(count / page_limit)
    newurl = store_endpoint
    for i in range(count):
        async with httpx.AsyncClient() as client:
            response = await client.get(newurl, headers=headers)
            result = response.json()
            await insert(result['products'])
            if 'next' in response.links:
                newurl = response.links['next']['url']
            # print(newurl)

                # print(response.links)
    return "Success"

User_History = []
Bot_History = []

@app.post("/chat/")
async def chat(reqeust: Request):
    conn = sqlite3.connect(r"./db/product.db")
    cur = conn.cursor()
    body = await reqeust.json()
    query = body['query']
    
    # if query in greetings:
    global User_History, Bot_History
    lan = translator.detect(query).lang

    print(translator.translate(query, dest = "en"))
    query = translator.translate(query, dest = "en").text

    

    customized_input = greeting(query)
    
    if customized_input[0] == "Yes" :
        return {"message" : translator.translate("Hi, I'm Hectool Assistant. How can I help you?", dest = lan).text}
    elif query.lower() in [greeting.lower() for greeting in greetings]:
        return {"message" : translator.translate("Hi, I'm Hectool Assistant. How can I help you?", dest = lan).text}
    else :

        if customized_input[2].lower() == "yes":
            query = customized_input[1]
            additional_query = """You are brilliant chatbot.The following content is Chat History."""
            temp = additional_query

            for i in range(len(User_History)-1, -1, -1):
                temp += f"User Question : {User_History[i]}\n Your Answer : {Bot_History[i]}\n"
                if len(re.findall(r'\w+', temp)) > token_limit: break
                additional_query = temp

            additional_query += "User Question : "
            query = additional_query + query

            try : 
                res = db_chain(query)
                steps = res['intermediate_steps']
                # text = steps[0]['input']
                text = steps[2]['sql_cmd']
                coulmns = []

                if "*" in text:
                    query = "PRAGMA table_info('products')"
                    cur.execute(query)
                    coulmns = [row[1] for row in cur.fetchall()]
                else :
                    coulmns = text.split("SELECT ")[1].split("FROM")[0].split(", ")
                    
                results = ast.literal_eval(res["result"])

                if len(results) == 0:
                    message = f"Question:{body['query']} and Result: None"
                    
                else : 
                    message = f"Question:{body['query']} and Result about Question is the following. Coulmns are {coulmns}\n And rows are"
                    for rlt in results:
                        temp = message + str(rlt)
                        if len(re.findall(r'\w+', temp)) > token_limit: break
                        message += str(rlt) + "\n"
                    
            except : 
                message = body['query']

            prompt = """With the above content, make readable and clear answer like human. Must not be ambigous. Should not mention about columns. And the final Answer should be more and more structured and configured so that the answer would be possible simple, but it should contain whole meanings. And If not necessary, If user are not asking, don't mention about id, type, form, ref_no, bore, shape, diameter_min, diameter_max, diameter_step, vendor, size, link, and name."""
            messages = [ {"role": "system", "content": "You are Hector, the dedicated personal shopper for Hectool. With years of experience and a vast knowledge of industrial/technical products, you pride yourself on your ability to guide users seamlessly through their shopping journey. Your demeanor is always friendly, attentive, and patient, ensuring every user feels valued and understood. You have a knack for understanding user needs, offering insightful recommendations based on the specifics they provide. Always ready to dive into the details, you are keen to share product specifications, comparisons, and insightful tidbits when prompted. However, you understand the importance of simplicity, so you avoid overwhelming users with technical jargon unless they specifically ask for in-depth details. Your ultimate goal is to be a beacon of support and information, ensuring every Hectool customer finds exactly what they're looking for, while also discovering new solutions they might not have considered. Always prioritize user needs, provide detailed product information when prompted, and avoid being overly technical unless the user asks for specifics."} ]

            message = message + prompt
            print(message)
            if message:
                messages.append(
                    {"role": "user", "content": message},
                )
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
            reply = chat.choices[0].message.content
            reply = translator.translate(reply, dest = lan).text
            User_History.append(body['query'])
            Bot_History.append(reply)
            chat_db["chat_history"].insert(
            {"role": "user", "content": query, "time": str(datetime.now())}
            )
            chat_db["chat_history"].insert(
            {"role": "bot", "content": reply, "time": str(datetime.now())}
            )
            return {"message": reply}
        else :
            user_question = customized_input[1]
            chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=[{
                        "role": "user",
                        "content": user_question
                    }]
                )
            reply = chat.choices[0].message.content

            return {"message": reply}

@app.get("/download-db/")
async def download_database():
    # Define the path to the database file
    db_file_path = "./db/chathistory.db"

    # Check if the file exists
    import os
    if not os.path.exists(db_file_path):
        raise HTTPException(status_code=404, detail="Database file not found")

    # Return the database file as a response with a specific filename
    return FileResponse(db_file_path, filename="chathistory.db")