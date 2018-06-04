# webhook.py
# coding=utf-8

import os
import ast
import random
import DB_connection as DB
import numpy as np

session = dict()
err2cat = ['食品安全','医药健康','科学技术','日常生活','诈骗类','谣言类'] #序号和类别的对应信息

def category(err_rate):
	err = []
	for x,y in err_rate:
		if y == 0:
			err.append(0)
		else:
			err.append(x/y)
	sum = np.sum(err)+0.05*len(err)
	prob = [(i+0.05)/sum for i in err]
	ran = np.random.random_sample()
	global err2cat
	j = 0
	for i in prob:
		if ran <= i:
			return j
		else:
			ran -= i
			j += 1

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
		print(post_dict)
		global session
		global err2cat
		if '考考我' in post_dict['utterance']:  # 欢迎语句
			err_rate = [[0,0],[0,0]]
			cat_id = category(err_rate)
			rank = DB.get_rank(1000, 0)
			qid, problem = DB.get_question(err2cat[cat_id])
			# problem_id, category, score, last sentence, bonus, (错误的题目数/总题数), rank
			session[post_dict['sessionId']] = [qid, cat_id, 1000,'欢迎使用‘考考我挑战版’，您可以在任意时刻回复“天猫精灵，使用说明”来了解如何使用该功能。下面，请听题：'+problem+'这是真的吗？', 0, err_rate, rank]
			return [bytes(output_form_2%('欢迎使用‘考考我挑战版’，您可以在任意时刻回复“天猫精灵，使用说明”来了解如何使用该功能。下面，请听题：'+problem+'这是真的吗？'),'utf-8')]
		elif '退出' in post_dict['utterance']:
			pt = session[post_dict['sessionId']][2]
			rank = DB.get_rank(pt, 1)
			if rank != -1:
				response = '本次测试，您的成绩是%d，排名%d。感谢使用本功能，期待与您的下次相遇。'%(pt, rank)
			else:
				response = '本次测试，您的成绩是%d，但未上榜。请继续加油，我期待与您的下次相遇。'%(pt)
			session.pop(post_dict['sessionId'])
			return [bytes(output_form%(response),'utf-8')]
		elif post_dict['utterance'] == '下一题':  # 出题
			cat = category(session[post_dict['sessionId']][5])
			qid, problem = DB.get_question(err2cat[cat])
			session[post_dict['sessionId']][0] = qid
			session[post_dict['sessionId']][1] = cat
			session[post_dict['sessionId']][3] = problem+'这是真的吗？'
			return [bytes(output_form_2%(problem+'这是真的吗？'), 'utf-8')]
		elif '是' in post_dict['utterance']  or '真' in post_dict['utterance'] or '假' in post_dict['utterance']:
			# 语句泛化部分
			if '不' in  post_dict['utterance'] :
				if '假' in post_dict['utterance']:
					user_answer = '是'
				else:
					user_answer = '不是'
			else:
				if '假' in post_dict['utterance']:
					user_answer = '不是'
				else:
					user_answer = '是'
			if user_answer == DB.get_answer(session[post_dict['sessionId']][0]):
				# 更新错误率
				cat = session[post_dict['sessionId']][1]
				session[post_dict['sessionId']][5][cat][1]+=1
				# 连续答对的题目数量
				session[post_dict['sessionId']][4] += 1
				## 更新分数，排名
				# 有bonus
				if session[post_dict['sessionId']][4] >= 5:
					score_update = DB.get_points(session[post_dict['sessionId']][0],1)+ 5*(session[post_dict['sessionId']][4]-4)
					new_rank = DB.get_rank(session[post_dict['sessionId']][2]+score_update,0)
					# 两次排名都上榜了
					if session[post_dict['sessionId']][6]!=-1:
						answer = '回答正确！您已连续答对%d道题，您的分数增加%d，您已进入排行榜，排名上升%d位。'%(session[post_dict['sessionId']][4],score_update, session[post_dict['sessionId']][6]-new_rank)+'   请听下一题：'
					# 有一次没上榜，不说排名变化
					else:
						answer = '回答正确！您已连续答对%d道题，您的分数增加%d。'%(session[post_dict['sessionId']][4],score_update)+'   请听下一题：'
					session[post_dict['sessionId']][2] = session[post_dict['sessionId']][2] + score_update # 更新分数
					session[post_dict['sessionId']][6] = new_rank # 更新排名
				# 没有bonus
				else:
					score_update = DB.get_points(session[post_dict['sessionId']][0],1)
					new_rank = DB.get_rank(session[post_dict['sessionId']][2]+score_update,0)
					# 两次排名都上榜了
					if session[post_dict['sessionId']][6]!=-1:
						answer = '回答正确！您的分数增加%d，排名上升%d位。'%(score_update, session[post_dict['sessionId']][6]-new_rank)+'   请听下一题：'
					# 有一次没上榜，不说排名变化
					else:
						answer = '回答正确！您的分数增加%d。'%score_update+'   请听下一题：'
					session[post_dict['sessionId']][2] = session[post_dict['sessionId']][2] + score_update # 更新分数
					session[post_dict['sessionId']][6] = new_rank # 更新排名
			else:
				# 更新错误率
				cat = session[post_dict['sessionId']][1]
				session[post_dict['sessionId']][5][cat][0]+=1
				session[post_dict['sessionId']][5][cat][1]+=1
				session[post_dict['sessionId']][4] = 0
				score_update = DB.get_points(session[post_dict['sessionId']][0],0)
				# 更新排名和分数
				session[post_dict['sessionId']][6] = DB.get_rank(session[post_dict['sessionId']][2]+score_update,0)
				session[post_dict['sessionId']][2] = session[post_dict['sessionId']][2] + score_update
				answer = '回答错误！请继续努力！这道题的解释是这样的：'+DB.get_reason(session[post_dict['sessionId']][0])+'。。请听下一题：'

			cat = category(session[post_dict['sessionId']][5])
			qid, problem = DB.get_question(err2cat[cat])
			session[post_dict['sessionId']][0] = qid
			session[post_dict['sessionId']][1] = cat
			answer = answer+problem+'这是真的吗？'
			session[post_dict['sessionId']][3] = answer
			return [bytes(output_form_2%(answer), 'utf-8')]

		elif post_dict['utterance']=='重听':
			return[bytes(output_form_2%(session[post_dict['sessionId']][3]), 'utf-8')]
		elif post_dict['utterance']=='使用说明':
			answer = "考考我挑战版以比赛的形式进行，退出时会给出排名和分数。连续答对还能有额外加分。我们会根据您每一类题目的正确率调整不同类别题目的出题的概率，答得越多，我们越了解您。在我解释错误原因时，您可随时打断我并说“天猫精灵，下一题”，即可跳过解释，直接进行下一题。任意时间回复“天猫精灵，重听”即可重听上一句话。任意时间回复“天猫精灵，退出”即可退出此技能。现在您可以回复“下一题”来继续答题。"
			return [bytes(output_form_2%(answer), 'utf-8')]
		else:
			session[post_dict['sessionId']][3] = '再说一次好吗？'
			return [bytes(output_form_2%('再说一次好吗？'), 'utf-8')]
	else:
		return [bytes(output_form_2%('再说一次好吗？'), 'utf-8')]
