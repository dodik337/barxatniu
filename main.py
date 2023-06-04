#imports
import os.path
import random
import sqlite3 as sq
from flask import Flask, redirect, url_for, render_template, g, request, session, flash
from config import Config
from database.sqldb import DataBase
import git

#variables
app = Flask(__name__)
app.config.from_object(Config)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'base.db'))) #creating database or connecting

def connect_db():
    conn = sq.connect(app.config['DATABASE'])
    conn.row_factory = sq.Row
    return conn

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
        return g.link_db

#Server updating
@app.route('/update_server', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/oduvanchik/barxatniu')
        origin = repo.remotes.origin
        origin.pull()
        return 'Сайт обновился', 200
    else:
        return 'Возникла ошибка', 400


#start page
@app.route('/', methods=['POST', 'GET'])
def start_page():
    db = connect_db()
    database = DataBase(db)
    #login
    if request.method == 'POST':
        if database.getUser(request.form['nick'], request.form['psw']):
            session['userlogged'] = request.form['nick']
        else:
            flash('Неверный логин или пароль', category='error')
    if 'userlogged' in session:
        return render_template('index.html', title='Главная', menu=database.getMenu(),\
                               status=database.getStatus(session['userlogged']))
    return render_template('index.html', title='Главная', menu=database.getMenu())

#register
@app.route('/register', methods=['POST', 'GET'])
def register():
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        return redirect(url_for('start_page'))
    if request.method == 'POST':
        if request.form['regpsw'] == request.form['regpsw2']:
            if int(request.form['age']) <= 20 and request.form['radio'] == 'teacher':
                flash('Укажите корректный возраст', category='error')
            else:
                if database.addUser(request.form['regnick'], request.form['regpsw'], \
                                        request.form['age'], request.form['regname'], request.form['radio']):
                    session['userlogged'] = request.form['regnick']
                    return redirect(url_for('start_page'))
                else:
                    flash('Некорректные данные', category='error')
        else:
            flash('Пароли не совпадают', category='error')
    return render_template('register.html', title='Регистрация', menu=database.getMenu())

#game choice
@app.route('/game/<int:id_game>', methods=['POST' , 'GET'])
def game_choice(id_game):
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        return render_template('game_choice.html', menu=database.getMenu(),
                                title=database.getGame(id_game)['title'],
                                status=database.getStatus(session['userlogged']),
                                game=database.getGame(id_game), games=database.getGames(),
                                gameid=random.randint(0, 9999))
    return render_template('game_choice.html', title=database.getGame(id_game)['title'], 
                                menu=database.getMenu(),
                                game=database.getGame(id_game), games=database.getGames(),
                                gameid=random.randint(0, 9999))

#connect to game
@app.route('/game/<gc>/<int:gameid>', methods=['POST', 'GET'])
def game(gc, gameid):
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        return render_template('game.html', menu=database.getMenu(),
                                status=database.getStatus(session['userlogged']),
                                gameid=random.randint(0, 9999))
    return render_template('game.html', menu=database.getMenu(),
                           gameid=random.randint(0, 9999))

#admin page
@app.route('/admin', methods=['POST', 'GET'])
def admin_page():
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        if database.getStatus(session['userlogged']) == 'admin':
            return render_template('admin.html', menu=database.getMenu(),\
                                    status=database.getStatus(session['userlogged']))
    return redirect(url_for('start_page'))

#reports
@app.route('/reports', methods=['POST', 'GET'])
def reports_page():
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        if request.method == 'POST':
            if database.addReport(session['userlogged'],
                                  request.form['about'],
                                  request.form['name']):
                flash('Спасибо за вклад в будущее сайта!', category='success')
                return redirect(url_for('reports_page'))
        return render_template('reports.html', title='Репорты', menu=database.getMenu(),
                                status=database.getStatus(session['userlogged']),
                                reports_unsolved=database.getUnSolvedReports(),
                                reports_solved=database.getSolvedReports(), reports=database.getReports(),
                                lastreps=database.getLastReports())
    return render_template('reports.html', title='Репорты', menu=database.getMenu(), reports=database.getReports(),
                            lastreps=database.getLastReports(),
                            reports_unsolved=database.getUnSolvedReports(),
                            reports_solved=database.getSolvedReports())

#report page
@app.route('/reports/<int:id_rep>', methods=['POST', 'GET'])
def showReport(id_rep):
    db = connect_db()
    database = DataBase(db)
    title = database.getReport(id_rep)['name']
    if 'userlogged' in session:
        if request.method == 'POST':
            if database.addAnswers(session['userlogged'], request.form['text'], id_rep):
                return render_template('report_page.html', title=title, menu=database.getMenu(),
                                       status=database.getStatus(session['userlogged']),
                                       report=database.getReport(id_rep),
                                       reports=database.getReports(),
                                       lastreps=database.getLastReports(),
                                       answers=database.getAnswers(id_rep))
        return render_template('report_page.html', title=title, menu=database.getMenu(),
                                status=database.getStatus(session['userlogged']), report=database.getReport(id_rep),
                                reports=database.getReports(),
                                lastreps=database.getLastReports(),
                                answers=database.getAnswers(id_rep))
    return render_template('report_page.html', title=title, menu=database.getMenu(), report=database.getReport(id_rep),
                            reports=database.getReports(),
                            lastreps=database.getLastReports(),
                            answers=database.getAnswers(id_rep))

#solving report
@app.route('/reports/solve/<int:id_rep>', methods=['POST', 'GET'])
def report_solve(id_rep):
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        if database.getReport(id_rep)['user'] == session['userlogged'] or \
            database.getStatus(session['userlogged'] == 'admin'):
            database.UpdateReportStatus(id_rep)
            return redirect(url_for('reports_page'))
    return redirect(url_for('reports_page'))

#Deleting report
@app.route('/delreport/<int:id_rep>')
def delreport(id_rep):
    db = get_db()
    database = DataBase(db)
    if 'userlogged' in session:
        if database.getStatus(session['userlogged']) == 'admin':
            if database.delReports(id_rep):
                return redirect(url_for('reports_page'))
    else:
        return redirect(url_for('start_page'))

#quit
@app.route('/quit')
def quit():
    if 'userlogged' in session:
        return redirect(url_for('start_page')), session.clear()
    else:
        return redirect(url_for('start_page'))

#contact
@app.route('/contact', methods=['POST', 'GET'])
def contact_page():
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        return render_template('contact.html', menu=database.getMenu(),\
                                status=database.getStatus(session['userlogged']))
    return render_template('contact.html', menu=database.getMenu())

#game list
@app.route('/game_list', methods=['POST', 'GET'])
def game_list():
    db = connect_db()
    database = DataBase(db)
    if 'userlogged' in session:
        return render_template('game_list.html', title='Список игр', menu=database.getMenu(),\
                                games=database.getGames(),
                                status=database.getStatus(session['userlogged']))
    return render_template('game_list.html', title='Список игр', menu=database.getMenu(), games=database.getGames())

if __name__ == "__main__":
    app.run(debug=True)