# -*- encoding: utf-8 -*-

import copy
import time

import requests


class AnswerQuestions:

    def __init__(self, x_token):
        self.x_token = x_token
        self.host = 'https://schapi.xkwell.com'

        self.headers = {
            'origin': 'https://zqxylive.xkwell.com',
            'referer': 'https://zqxylive.xkwell.com',
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

    def get_normal_paper_list(self):
        """
        获取试卷列表
        """
        url = self.host + '/api/GetNormalPaperList'
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token

        response = requests.get(url, headers=headers)
        return response.json()['data']

    def get_paper_card(self, answerid):
        """
        获取试题列表
        """
        url = self.host + '/api/GetPaperCard?answerid=' + answerid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        response = requests.get(url, headers=headers)
        return response.json()['data'][0]['tklist']

    def update_user_paper_answer(self, answerid, tkid, useranswer):
        """
        更新答案
        """
        url = self.host + '/api/UpdateUserPaperAnswer'
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token

        data = {
            "answerid": answerid,
            "tkid": tkid,
            "useranswer": useranswer
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            print(response.text)

    def finsh_paper_answer(self, answerid):
        """
        提交试卷
        """
        url = self.host + '/api/FinshPaperAnswer?answerid=' + answerid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        response = requests.post(url, headers=headers)
        print('提交试卷:', response.text)
        if response.status_code != 200:
            print(response.text)

    def create_paper_answer(self, scoreid):
        """
        创建试卷答案
        """
        url = self.host + '/api/CreatePaperAnswer?type=2&answerid=' + scoreid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        headers['authority'] = 'schapi.xkwell.com'
        headers['method'] = 'GET'
        headers['path'] = '/api/CreatePaperAnswer?answerid=' + scoreid + '&type=2'

        response = requests.post(url, headers=headers)
        if response.status_code != 200:
            print(response.text)

    def get_paper_tk_analysis(self, answerid, tkid):
        """
        获取试题答案
        """
        url = self.host + '/api/GetPaperTkAnalysis?answerid=' + answerid + '&tkid=' + tkid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        response = requests.get(url, headers=headers)
        return response.json()['data']

    def run(self):
        skip = [
            '749a1e42-6254-47eb-8097-764e0e811385',
            'a959f8cd-349e-403f-9e20-3575bef39829'
        ]

        paper_list = self.get_normal_paper_list()

        for paper in paper_list:
            title = paper['title']
            scoreid = paper['scoreid']

            if scoreid in skip:
                continue

            self.create_paper_answer(scoreid)

            tk_list = self.get_paper_card(scoreid)
            for tk in tk_list:
                tkid = tk['tkid']
                tk_analysis = self.get_paper_tk_analysis(scoreid, tkid)

                tk_title = tk_analysis['title']
                tkanswer = tk_analysis['tkanswer']
                tk_content = tk_analysis['content']

                print('==' * 30)
                print('试卷名称:', title)
                print('试题名称:', tk_title)
                print('试题内容: ')
                for c in tk_content:
                    print(c)
                print('正确选项: ', tkanswer)

                self.update_user_paper_answer(scoreid, tkid, tkanswer)
                time.sleep(0.5)

            self.finsh_paper_answer(scoreid)


class Exam:

    def __init__(self, x_token):
        self.x_token = x_token
        self.host = 'https://schapi.xkwell.com'

        self.headers = {
            'authority': 'schapi.xkwell.com',
            'scheme': 'https',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'origin': 'https://zqxylive.xkwell.com',
            'priority': 'u=1, i',
            'referer': 'https://zqxylive.xkwell.com/',
            'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site'
        }

    def get_exam_paper_list(self):
        url = self.host + '/api/GetExamPaperList'
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        headers['path'] = '/api/GetExamPaperList'

        response = requests.get(url, headers=headers)
        return response.json()['data']

    def get_paper_card(self, answerid):
        """
        获取试题列表
        """
        url = self.host + '/api/GetPaperCard?answerid=' + answerid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        response = requests.get(url, headers=headers)
        return response.json()['data'][0]['tklist']

    def create_paper_answer(self, scoreid):
        """
        创建试卷答案
        """
        url = self.host + '/api/CreatePaperAnswer?type=2&answerid=' + scoreid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        headers['authority'] = 'schapi.xkwell.com'
        headers['method'] = 'GET'
        headers['path'] = '/api/CreatePaperAnswer?answerid=' + scoreid + '&type=2'

        response = requests.post(url, headers=headers)
        if response.status_code != 200:
            print(response.text)

    def get_paper_tk_analysis(self, answerid, tkid):
        """
        获取试题答案
        """
        url = self.host + '/api/GetPaperTkAnalysis?answerid=' + answerid + '&tkid=' + tkid
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token
        response = requests.get(url, headers=headers)
        return response.json()['data']

    def update_user_paper_answer(self, answerid, tkid, useranswer):
        """
        更新答案
        """
        url = self.host + '/api/UpdateUserPaperAnswer'
        headers = copy.deepcopy(self.headers)
        headers['x-token'] = self.x_token

        data = {
            "answerid": answerid,
            "tkid": tkid,
            "useranswer": useranswer
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            print(response.text)

    def run(self):
        paper_list = self.get_exam_paper_list()
        for paper in paper_list:
            title = paper['title']
            scoreid = paper['scoreid']
            tk_list = self.get_paper_card(scoreid)

            if title != '移动应用开发 2025第二学期 期末考试':
                continue

            for tk in tk_list:
                tkid = tk['tkid']
                tk_analysis = self.get_paper_tk_analysis(scoreid, tkid)

                tk_title = tk_analysis['title']
                tkanswer = tk_analysis['tkanswer']
                tk_content = tk_analysis['content']

                print('==' * 30)
                print('试卷名称:', title)
                print('试题名称:', tk_title)
                print('试题内容: ')
                for c in tk_content:
                    print('  ', c)
                print('正确选项: ', tkanswer)
                self.update_user_paper_answer(scoreid, tkid, tkanswer)
                time.sleep(0.5)

            break


if __name__ == '__main__':
    X_TOKEN = 'lQ6Dqe1IOmbEg0BPb9zjPSdrbF20260110110401'
    # obj = AnswerQuestions(X_TOKEN)
    # obj.run()

    ex = Exam(X_TOKEN)
    ex.run()
