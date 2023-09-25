import openai
import os
from dotenv import load_dotenv

import json

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

messages = [ 
    {"role": "system", 
     "content": "You are a great bot that tailors user's questions."} ]

def greeting(query):
    try:
        message = query + """

---

Above is the question of user.
Once you have considered the examples and conditions below, you should tailor and tailor this question according to the rules below.

1) Now condition:

I have one SQL database and my products are stored there.
Users will have questions to search for these products or information.

 - Name of the product: [Clamping Heads, F-Type Standard Collets],
 - Product parameters: [bore, shape, diameter, vendor, link, name]

2) Tailor Rules:
    - Sometimes users used unanswerable questions about these product names and parameters.
      For example, if your question is 'I'm looking for the URL for an f type collet', you should customize it to something like 'I'm looking for a link for an F-Type Standard Collets' using correct grammar and correct strings and the correct product name and corresponding parameters.
      If the raw question does not contain product names or similar parameters that are similar to the product name and product parameters in the SQL of above condition, you do not need to customize the question.
      And also, if user have question like these `what tools (products) do you have (sell or service)?`, you have to customize like `What types of products do you have?`.
    - If the question is meant to be a greeting such as "hello" or "how are you" you should add a "greeting" flag, if not,  you should add a "no-greeting" flag.
    - If the question is another "no-greeting" that is not related to the question in the first rule, you should add a "no" flag. If not, you should add a "yes" flag.
      For example, if the question is "What is the URL of the clamping head" or "what tools (products) do you sell or have?", you should add a "yes" flag.
      But 'what is a clamping head?' Or for questions like 'Which countries have the most Type F collets?', you don't need to customize it, you just need to add the "no" flag.
      In specific cases, 'Are you done? ` or `is it all?`, in this case you need to add the "yes" flag.
      Because the outcome of such a question depends on the product of the previous question.

Based on above condition and rules, the output should be like this structure:

`
{
    "type": result of second rule: "greeting" or "no-greeting",
    "result" : result of first rule: that is customized question,
    "sql": result of third rule: "yes" or "no"
}

`


"""
        
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-4", messages=messages
        )
        reply = chat.choices[0].message.content
        query_result = reply.split("{")[1]
        query_result = query_result.split("}")[0]
        reply = "{ " + query_result + " }" 
        json_reply = json.loads(reply)
        print("~~~~~~~~~~")
        print(json_reply)
        print("~~~~~~~~~~~~~")
        if json_reply['type'].lower() == "greeting":
            return ["Yes", json_reply['result'], json_reply['sql']];
        else: return ["No", json_reply['result'], json_reply['sql']];
    except:
        return "Error";