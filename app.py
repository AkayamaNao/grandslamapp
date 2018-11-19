#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, session, request, redirect, render_template, url_for
import pandas as pd
import time

app = Flask(__name__)
# cookie を暗号化する秘密鍵 (本来はランダムに作る)
app.config['SECRET_KEY'] = 'jhsdjhfalnsndushduvhjzkdhvjzbxcvskudhlisuegliguhre98wy58twhu45ruifh3uib4lig'

# 各 route() 関数の前に実行される処理
@app.before_request
def before_request():
    # セッションに username が保存されている (= ログイン済み)
    if session.get('username') in list(user_info['user_id']):
        return
    # リクエストがログインページに関するもの
    if request.path == '/login':
        return
    if request.path == '/account':
        return
    # ログインされておらずログインページに関するリクエストでもなければリダイレクトする
    return redirect('/login')


@app.route('/', methods=['GET'])
def index():
    event = pd.read_csv('data/event.csv', header=0, encoding="SHIFT-JIS")
    event=event.sort_values(by='timestamp' ,ascending=False)
    event=event.fillna('')
    event_list=[]
    for index, row in event.iterrows():
        try:
            user_name = user_info[user_info['user_id'] == row['organizer']]['name'].item()
        except:
            user_name='unknown'
        event_list.append({'id': row['id'], 'title': row['title'],  'date': row['date'] , 'start': row['start'],'organizer': row['organizer'],'user_name':user_name, 'memo': row['memo']})
    return render_template('index.html',event=event_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # ログイン処理
    if request.method == 'POST':
            # セッションにユーザ名を保存してからインデックスページにリダイレクトする
            user_id = request.form['user_id']
            password=request.form['password']
            if user_id in list(user_info['user_id']):
                if user_info[user_info['user_id']==user_id]['password'].item() == password:
                    session['username'] = user_id
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error=u'パスワードが違います')
            else:
                return render_template('login.html',error=u'現在そのユーザーは使われていません')
    else:
        return render_template('login.html')

@app.route('/account', methods=['GET','POST'])
def account():
    if request.method == 'POST':
            user_id = request.form['user_id']
            password=request.form['password']
            name = request.form['name']
            if len(user_id)*len(password)*len(name) < 1:
                return render_template('account.html', error=u'すべて入力してください')
            if user_id in list(user_info['user_id']):
                return render_template('account.html', error=u'そのIDは既に使われています')
            if len(password)<6:
                return render_template('account.html', error=u'パスワードは6文字以上にしてください')
            tmp = pd.DataFrame([[user_id, int(time.time()),password,name,0]],columns=['user_id','timestamp','password','name','car_max'])
            tmp.to_csv('data/user.csv', mode='a', header=False, index=False, encoding="SHIFT-JIS")
            global user_info
            user_info=user_info.append(tmp)
            session['username'] = user_id
            return redirect(url_for('index'))
    else:
        return render_template('account.html')


@app.route('/logout', methods=['GET'])
def logout():
    #セッションからユーザ名を取り除く (ログアウトの状態にする)
    session.pop('username', None)
    # ログインページにリダイレクトする
    return redirect(url_for('login'))

@app.route('/add', methods=['GET','POST'])
def add():
    if request.method == 'POST':
            title = request.form['title']
            date=request.form['date']
            start = request.form['start']
            memo = request.form['memo']
            if title != '':
                event = pd.read_csv('data/event.csv', header=0, encoding="SHIFT-JIS")
                tmp=pd.DataFrame([[int(event.max()['id'])+1, int(time.time()), title, date, start,session.get('username'), memo]], columns=event.columns)
                tmp.to_csv('data/event.csv',mode='a',header=False,index=False, encoding="SHIFT-JIS")
                return redirect(url_for('index'))
            else:
                return render_template('add.html', error=u'タイトルを入力してください')
    else:
        return render_template('add.html')

@app.route('/mypage', methods=['GET','POST'])
def mypage():
    if request.method == 'POST':
        car_max = int(request.form['car_max'])
        global user_info
        user_info.loc[user_info['user_id'] == session.get('username'), 'car_max'] = car_max
        user_info.to_csv('data/user.csv', index=False, encoding="SHIFT-JIS")
        user_name = user_info[user_info['user_id'] == session.get('username')]['name'].item()
        return render_template('mypage.html', user_name=user_name, car_max=car_max)
    else:
        user_name=user_info[user_info['user_id']== session.get('username')]['name'].item()
        car_max=user_info[user_info['user_id']== session.get('username')]['car_max'].item()
        return render_template('mypage.html',user_name=user_name ,car_max=car_max)

@app.route('/event/<int:id>', methods=['GET','POST'])
def event(id):
    # if request.method == 'POST':

    event = pd.read_csv('data/event.csv', header=0, encoding="SHIFT-JIS")
    event = event.fillna('')
    event = event[event['id'] == id]
    user_name = user_info[user_info['user_id'] == event['organizer'].item()]['name'].item()
    event = {'id': event['id'].item(), 'title': event['title'].item(), 'date': event['date'].item(),
             'start': event['start'].item(), 'organizer': event['organizer'].item(), 'user_name': user_name,
             'memo': event['memo'].item()}
    log = pd.read_csv('data/log.csv', header=0, encoding="SHIFT-JIS")
    log = log[log['event_id'] == id]
    log = log.sort_values(by='timestamp', ascending=False)
    ride=0
    if session.get('username') in list(log['user']):
        log_id = log.loc[log['user'] == session.get('username'), 'id'].item()
        if log.loc[log['user'] == session.get('username'), 'driver'].isnull().item():
            ride = 1
    else:
        log_id=-1
        ride=1

    driver=1
    join=1
    if session.get('username') in list(log['user']):
        join=0
        if log[log['user'] == session.get('username')]['car_max'].item() != 0:
            driver=0

    log_list = []
    for index, row in log.iterrows():
        flag=0
        if row['car_max'] != 0:
            try:
                member = log[log['driver'] == row['user']]['user']
            except:
                member=[]
            member_list=list(member)
            if len(member) > 0:
                if len(member) >= int(row['car_max']):
                    flag = 2
                else:
                    flag = 1
                member = ','.join([user_info[user_info['user_id'] == x]['name'].item() for x in member])
                member = u'車 : ' + member + ' / ' + str(int(row['car_max'])) + u'人'
            else:
                flag = 1
                member = u'車 : 0 / ' + str(int(row['car_max'])) + u'人'
            if ride == 0:
                flag=2
            if session.get('username') in member_list:
                flag=3
        else:
            member = ''
        log_list.append({'user_id': row['user'],'user_name':  user_info[user_info['user_id'] == row['user']]['name'].item(), 'member': member, 'flag': flag})
    return render_template('event.html', log_id=log_id, event=event, log=log_list, num=len(log_list),driver=driver,join=join)

@app.route('/join/<int:id>', methods=['GET'])
def join(id):
    log = pd.read_csv('data/log.csv', header=0, encoding="SHIFT-JIS")
    try:
        num=int(log.max()['id']) + 1
    except:
        num=0
    tmp = pd.DataFrame(
        [[num,id, int(time.time()),session.get('username'),user_info[user_info['user_id'] == session.get('username')]['car_max'].item(),'']],
        columns=log.columns)
    tmp.to_csv('data/log.csv', mode='a', header=False, index=False, encoding="SHIFT-JIS")
    return redirect('/event/'+str(id))

@app.route('/joindel/<int:id>', methods=['GET'])
def joindel(id):
    log = pd.read_csv('data/log.csv', header=0, encoding="SHIFT-JIS")
    event_id = log.loc[log['id'] == id, 'event_id'].item()
    log = log.loc[log['id'] != id]
    log.to_csv('data/log.csv', index=False, encoding="SHIFT-JIS")
    return redirect('/event/' + str(event_id))

@app.route('/ride/<string:tmp>', methods=['GET'])
def ride(tmp):
    tmp=tmp.split(',')
    id=int(tmp[0])
    driver=tmp[1]
    log = pd.read_csv('data/log.csv', header=0, encoding="SHIFT-JIS")
    event_id=log.loc[log['id'] == id, 'event_id'].item()
    log.loc[log['id'] == id, 'driver'] = driver
    log.to_csv('data/log.csv', index=False, encoding="SHIFT-JIS")
    return redirect('/event/'+str(event_id))

@app.route('/ridedel/<int:id>', methods=['GET'])
def ridedel(id):
    log = pd.read_csv('data/log.csv', header=0, encoding="SHIFT-JIS")
    event_id=log.loc[log['id'] == id, 'event_id'].item()
    log.loc[log['id'] == id, 'driver'] = ''
    log.to_csv('data/log.csv', index=False, encoding="SHIFT-JIS")
    return redirect('/event/'+str(event_id))

if __name__ == '__main__':
    user_info = pd.read_csv('data/user.csv', header=0, encoding="SHIFT-JIS")
    app.run(debug=True)