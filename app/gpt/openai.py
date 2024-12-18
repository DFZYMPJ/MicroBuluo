import os

from openai import OpenAI

#第三方请求工具
import requests

#json工具可以将字典转为json规范的格式
import json

#随机数生成器
from random import sample

class Simsimi():

    def __init__(self,question): 
        self.question = question


    def Talk(self):

        # 定义变量地址
        url = "https://www.simsimi.com/api/chats?lc=ch&ft=1&normalProb=2&reqText="+ self.question + "&talkCnt=9"

        # 伪装请求头
        ua = [
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) QQBrowser/6.9.11079.201',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        ]
        #临时回话密钥列表
        key = [
            's%3A0NRtUecEnXKXDCOotiFHt2_vg1P-uqN6.c%2F0n0TstVdvPJrxdH%2F4XTr8XE8h7fxoC2PSh2%2F%2Fg2Ps',
            's%3Aq1INv4ckPz3UHDUuFXz3uJQubibtLV_5.sf8dBFnj%2F6zOiCc4ukmF20q1PkYvjkc45ULhG0WfUuE',
            's%3Ag73SySymbJLZVKqhh1sKCjSJJpck25Td.TJvONBKd1olrOFBmf4G7Ja52cCWFse553axE7i%2Fzcms',
            's%3AK0mbRmxKdGZ7WiE_LpRGnnANh954pfU2.RZMe70ThqDwL6HQWak%2BG96ZwvEhQ7n%2BQTGT42iS%2FSns'
        ]
        cookies = {
            '_gid': 'GA1.2.920356614.1703316302',
            '_ga_6WWF7N9DCV': 'GS1.2.1703316302.1.1.1703316444.0.0.0',
            '_ga': 'GA1.2.1443192985.1703316302',
            '_ga_3XSDZTHJM8': 'GS1.1.1703316446.1.1.1703316844.0.0.0',
            'dotcom_session_key': sample(key,1)[0],
            'languageCode': 'ch',
            'normalProb': '2',
            'doQuestion': 'true',
            'i18n_redirected': 'zh',
            '_gat': '1',
            '_ga_HCSLE92YB7': 'GS1.2.1703317259.1.1.1703318794.0.0.0',
            'currentChatCnt': '7',
            'bubbleCount': '100',
        }

        headers = {
            'authority': 'www.simsimi.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'if-none-match': '"63617-A6xmWm3XvjgwfPknFsaCRqF6jdU"',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': sample(ua,1)[0]
        }


        # 1.发起网络请求
        response = requests.get(url,cookies=cookies, headers=headers)

        #<Response>[200]：请求成功 
        #print(response)

        # 2.获取数据，.json()解析返回的数据
        json_data = response.json()
        #{type,count,respSentence}
        #print(json_data)

        name = [
            "小黄鸡",
            "冰墩墩",
            "学神之女",
            "DFZYMPJ",
            "小竹子",
        ]
        print(self.question, '\n' + json_data['respSentence'])
        message = {
        'msg':json_data['respSentence'],
        'username':sample(name,1)[0],
        'type':json_data['type'],
        'sid':"simsimi"
        }

        return message


class Eliza():
    
    def __init__(self,question): 
        self.question = question

    def Say(self):

        openai_client = OpenAI(
            base_url='http://localhost:5005/v1',
            api_key=os.environ.get('OPENAI_API_KEY', 'x'),
            )
        messages = [
            {"role": "system", "content": "You are a helpful assistant."}, ]

        stream = True  # set to False to get all responses at once
        
        messages.append({"role": "user", "content": self.question})
         # this returns the response all at once
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        response = completion.choices[0].message.content
        print('Eliza:', response)

        messages.append({"role": "assistant", "content": response})

        message = {
        'msg':response,
        'username':'Eliza',
        'type':'text',
        'sid':"simsimi"
        }

        return message
