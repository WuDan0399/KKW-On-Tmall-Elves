# webhook.py
# coding=utf-8

import os
import ast
import docx
import random
import DB_connection as DB

session = dict()
def application(environ, start_response):
	start_response('200 OK', [('Content-Type', 'text/html')])
	method = environ['REQUEST_METHOD']
	output_form = '{"returnCode": "0","returnErrorSolution": "","returnMessage": "","returnValue": {"reply":"%s","resultType": "RESULT","actions": [{"name": "audioPlayGenieSource","properties": {"audioGenieId": "123"}}],"properties": {},"executeCode": "SUCCESS","msgInfo": ""}}'
	output_form_2 = '{"returnCode": "0","returnErrorSolution": "","returnMessage": "","returnValue": {"reply":"%s","resultType": "ASK_INF","actions": [{"name": "audioPlayGenieSource","properties": {"audioGenieId": "123"}}],"properties": {},"executeCode": "SUCCESS","msgInfo": ""}}'
	if method == 'POST':
		try:
			request_body_size = int(environ.get('CONTENT_LENGTH', 0))
		except (ValueError):
			request_body_size = 0
		request_body = environ['wsgi.input'].read(request_body_size)
		post_dict = ast.literal_eval(str(request_body, encoding = 'utf8'))
		global session
		if '考考我' in post_dict['utterance']:  # 欢迎语句
			session[post_dict['sessionId']] = [0,'',1000,'欢迎使用‘考考我’，您可以回复“使用说明”来了解如何使用该功能。现在您是想做“谣言”类题目还是“诈骗”类题目？']
			return [bytes(output_form_2%('欢迎使用‘考考我’，您可以回复“使用说明”来了解如何使用该功能。现在您是想做“谣言”类题目还是“诈骗”类题目？'),'utf-8')]
		elif '退出' in post_dict['utterance']:
			response = '感谢使用本功能，再见。'
			session.pop(post_dict['sessionId'])
			return [bytes(output_form%(response),'utf-8')]
		elif '谣言' in post_dict['utterance']:
			qid, problem = DB.get_question('谣言类')
			session[post_dict['sessionId']][0:2] = [qid, '谣言类']
			session[post_dict['sessionId']][3] = problem+'这是真的吗？'
			return [bytes(output_form_2%(problem+'这是真的吗？'), 'utf-8')]
		elif '诈骗' in post_dict['utterance'] or '照片' in post_dict['utterance']:
			qid, problem = DB.get_question('诈骗类')
			session[post_dict['sessionId']][0:2] = [qid, '诈骗类']
			session[post_dict['sessionId']][3] = problem+'这是真的吗？'
			return [bytes(output_form_2%(problem+'这是真的吗？'), 'utf-8')]
		elif post_dict['utterance'] == '下一题':  # 出题
			if post_dict['sessionId'] not in session or session[post_dict['sessionId']][1]=='':
				return [bytes(output_form_2%('请先选择题型哦！可选择“谣言”或者“诈骗”'), 'utf-8')]
			qid, problem = DB.get_question(session[post_dict['sessionId']][1])
			session[post_dict['sessionId']][0] = qid
			session[post_dict['sessionId']][3] = problem+'这是真的吗？'
			return [bytes(output_form_2%(problem+'这是真的吗？'), 'utf-8')]
		elif '是' in post_dict['utterance']  or '真' in post_dict['utterance'] or '假' in post_dict['utterance']:
			if '不' in  post_dict['utterance'] :
				if '假' in post_dict['utterance']:
					post_dict['utterance'] = '是'
				else:
					post_dict['utterance'] = '不是'
			else:
				if '假' in post_dict['utterance']:
					post_dict['utterance'] = '不是'
				else:
					post_dict['utterance'] = '是'
			if post_dict['sessionId'] not in session or session[post_dict['sessionId']][0]==0:
				answer = '要先出题哦！'
			elif '您要听解释吗？' in session[post_dict['sessionId']][3]:
				answer = '不可以重复答题哦，您要听解释吗？'
			elif post_dict['utterance'] == DB.get_answer(session[post_dict['sessionId']][0]):
				answer = '回答正确！您要听解释吗？'
			else:
				answer = '回答错误！请继续努力！您要听解释吗？'
			session[post_dict['sessionId']][3] = answer
			return [bytes(output_form_2%(answer), 'utf-8')]
		elif '要' in post_dict['utterance']:
			if '不' in post_dict['utterance']:
				if post_dict['sessionId'] not in session or session[post_dict['sessionId']][0]==0:
					answer = '要先出题哦！'
				else:
					answer = '好哒！现在您可以回复“下一题”或题目类型。'
				session[post_dict['sessionId']][3] = answer
				return [bytes(output_form_2%(answer),'utf-8')]
			else:
				if post_dict['sessionId'] not in session or session[post_dict['sessionId']][0]==0:
					answer = '要先出题哦！'
				else:
					answer = DB.get_reason(session[post_dict['sessionId']][0])+'讲解完毕，现在您可以回复“下一题”或题目类型。'
				session[post_dict['sessionId']][3] = answer
				return [bytes(output_form_2%(answer), 'utf-8')]
		elif post_dict['utterance']=='重听':
			return[bytes(output_form_2%(session[post_dict['sessionId']][3]), 'utf-8')]
		elif post_dict['utterance']=='使用说明':
			answer = "每次进入技能后，请选择题目类型--“谣言”或“诈骗”。每道题目结束后，您可以直接说“下一题”，也可以重新选择题目类型，比如回复“谣言”。若您没听清解释或题目，可以回复“重听”可重听上一句话，回复“退出”即可退出此技能。在任意时刻回复“天猫精灵，下一题”，可跳过解释，直接进行下一题。现在您可以回复“下一题”来继续答题。"
			return [bytes(output_form_2%(answer), 'utf-8')]
		else:
			session[post_dict['sessionId']][3] = '再说一次好吗？'
			return [bytes(output_form_2%('再说一次好吗？'), 'utf-8')]
	else:
		return [bytes(output_form_2%('再说一次好吗？'), 'utf-8')]
