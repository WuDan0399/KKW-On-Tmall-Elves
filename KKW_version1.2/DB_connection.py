# coding=utf-8
import pymysql
import random
import datetime
class Connection(object):
    def connect_database(self):
        self.connection = pymysql.connect(host='localhost',
                                          user='root',
                                          db='kaokaoni',
                                          passwd='000000',
                                          charset="utf8"
                                          )
        self.cursor = self.connection.cursor()

    def disconnect_database(self):
        self.cursor.close()
        self.connection.close()

    def exec_query(self, sql):
        self.cursor.execute(sql)

    def exec_update(self, sql):
        self.cursor.execute(sql)
        self.connection.commit()

    def fetch_cursor(self):
        return self.cursor.fetchall()
""" 输入一个问题的id，输出问题对应的的正确率"""
def get_percent(qid):
    database = Connection()
    database.connect_database()
    database.exec_query("SELECT correct,wrong FROM accuracy WHERE qid = %d" % qid)
    values = database.fetch_cursor()
    database.disconnect_database()
    return (float(values[0][0])/(float(values[0][0])+float(values[0][1])))*100

""" 输入一个分数, state bool表示如果答题结束则为1，如果答题没结束（中途）则为0，输出一个排名, 返回 -1 则未上榜 """
def get_rank(point, state):
    database = Connection()
    database.connect_database()
    database.exec_query("SELECT * FROM rank")
    values = database.fetch_cursor()
    ranklist = [int(i[0]) for i in list(values)]
    ranklist.sort()
    if point <= ranklist[0]: return -1
    if state:
        database.exec_update("UPDATE rank SET pts = %d WHERE pts = %d LIMIT 1" %(point, ranklist[0]))
    database.exec_query("SELECT * FROM rank")
    values = database.fetch_cursor()
    ranklist = [int(i[0]) for i in list(values)]
    ranklist.sort()
    database.disconnect_database()
    i = 0
    while 1:
      if ranklist[i] >= point: break
      i = i+1
      if i>=len(ranklist):
          i = i-1
          break
    rank = len(ranklist)-i
    return rank
""" 更新正确率表格，在getpercent之前需要先更新本次的结果，输入为问题id与本次答对与否,答对cw为1，否则为0，qid int； cw bool """
def update_accuracy(qid, cw):
    database = Connection()
    database.connect_database()
    if cw:
        database.exec_update("UPDATE accuracy SET correct = correct + 1 WHERE qid = %d" %qid)
    else:
        database.exec_update("UPDATE accuracy SET wrong = wrong + 1 WHERE qid = %d" %qid)
    database.disconnect_database()
    return 0
""" 输入一个type，随机输出对应问题的（qid, 问题） tuple"""
def get_question(type):
    tmp = datetime.datetime.now()
    y = 20
    m = 0
    d = 0
    date = str(tmp.year-y)+'-'+str(tmp.month-m) + '-' + str(tmp.day-d)
    database = Connection()
    database.connect_database()
    database.exec_query("SELECT qid, question FROM questions WHERE type = '%s' AND time > '%s'"%(type, date))
    values = database.fetch_cursor()
    q_list = list(values)
    index = random.randint(0, len(q_list)-1)
    database.disconnect_database()
    return q_list[index]
"""输入一个qid，返回一个字符串 answer"""
def get_answer(qid):
    database = Connection()
    database.connect_database()
    database.exec_query("SELECT answer FROM questions WHERE qid = %d"%qid)
    values = database.fetch_cursor()
    database.disconnect_database()
    return values[0][0]
"""输入一个qid，返回一个字符串 reason"""
def get_reason(qid):
    database = Connection()
    database.connect_database()
    database.exec_query("SELECT reason FROM questions WHERE qid = %d"%qid)
    values =database.fetch_cursor()
    database.disconnect_database()
    return values[0][0]
""" 输入一个问题及其对应的答题结果，得到答题者应该获得的分数"""
def get_points(qid, cw):
    update_accuracy(qid, cw)
    if cw:
        return get_percent(qid)
    else:
        return get_percent(qid)-100
""" 输入一个问题的连续答对题数，得到答题者连续答对的bonus"""
def get_bonus(c):
    return c*10

""" 输入答题者类别错误率字典，返回与错误率相关的随机生成id,题目"""
def get_question_based_on_error_rate(error_rate_dict):
    constant = 0.1
    typelist = list(error_rate_dict.keys())
    ratelist = []
    s = 0
    for t in error_rate_dict:
        s += error_rate_dict[t]+0.1
        ratelist += [error_rate_dict[t] + 0.1]
    ratelist[0] = ratelist[0]/s
    for i in range(1, len(ratelist)):
        ratelist[i] = (ratelist[i]+ratelist[i-1])/s
    ratelist[-1] = 1.0
    u = random.uniform(0,1)
    i = 0
    while 1:
        if u < ratelist[i]:
            type = typelist[i]
            break
        i += 1
    return get_question(type)

if __name__ == '__main__':
    # update_accuracy(1, 1)
    # a = get_percent(1)
    # print(a)
    # b = get_question('电信类')
    # print(b)
    # c = get_rank(1080, 1)
    # print(c)
    # d = get_answer(b[0])
    # print(d)
    # e = get_reason(b[0])
    # print(e)
    f = get_question_based_on_error_rate({'谣言类':0.9, '诈骗类':0.1})
    print(f)
