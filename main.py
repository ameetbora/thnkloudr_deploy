from flask import Flask
from config import Config
# import datetime
import sqlite3
import symbl
import time as t
# import json
import os
from werkzeug.utils import secure_filename
from datetime import time
from datetime import date
from datetime import datetime
from datetime import timedelta
import json
import enum
from trello import TrelloClient

from flask import render_template, redirect, url_for, abort, request, jsonify, flash

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
# from flask_wtf.html5 import URLField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, url, Length

app = Flask(__name__)
app.config.from_object(Config)


class TestCycleForm(FlaskForm):
    testcyclename = StringField('Test Cycle Name', validators=[DataRequired(), Length(min=0, max=40)])
    testcycledesc = StringField('Test Cycle Description', validators=[DataRequired(), Length(min=0, max=300)])
    projectname = StringField('Project Name', validators=[DataRequired(), Length(min=0, max=40)])
    projectdesc = StringField('Project Description', validators=[DataRequired(), Length(min=0, max=300)])
    trellolink = URLField('Enter Trello Board', validators=[url()])
    testcycleimage = FileField('Image', validators=[
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    createtestcycle = SubmitField('Create')


class TestItemForm(FlaskForm):
    testitemname = StringField('Test Name', validators=[DataRequired(), Length(min=0, max=40)])
    testitemdesc = StringField('Test Cycle Description', validators=[DataRequired(), Length(min=0, max=150)])
    testvideo = FileField('Upload Video', validators=[
        FileAllowed(['mp4'], 'mp4 files only')
    ])
    submit = SubmitField('Create')


class TestItemUpdateForm(FlaskForm):
    testitemname = StringField('Test Name', validators=[DataRequired(), Length(min=0, max=40)])
    testitemdesc = StringField('Test Cycle Description', validators=[DataRequired(), Length(min=0, max=300)])
    testvideo = FileField('Upload Video', validators=[
        FileAllowed(['mp4'], 'mp4 files only')
    ])
    submit = SubmitField('Update')


class TestCycleUpdateForm(FlaskForm):
    testcyclename = StringField('Test Cycle Name', validators=[DataRequired(), Length(min=0, max=40)])
    testcycledesc = StringField('Test Cycle Description', validators=[DataRequired(), Length(min=0, max=300)])
    projectname = StringField('Project Name', validators=[DataRequired(), Length(min=0, max=40)])
    projectdesc = StringField('Project Description', validators=[DataRequired(), Length(min=0, max=300)])
    trellolink = URLField('Enter Trello Board', validators=[url()])
    testcycleimage = FileField('Image', validators=[
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    createtestcycle = SubmitField('Update')


def to_serializable(val):
    """JSON serializer for objects not serializable by default"""

    if isinstance(val, (datetime, date, time)):
        return val.isoformat()
    elif isinstance(val, enum.Enum):
        return val.value
    elif hasattr(val, '__dict__'):
        return val.__dict__

    return val


def to_json(data):
    """Converts object to JSON formatted string"""

    return json.dumps(data, default=to_serializable)


def get_db_connection():
    dbpath = app.root_path + '/db/' + app.config['DB_NAME']
    # print(dbpath)
    conn = sqlite3.connect(dbpath)
    conn.row_factory = sqlite3.Row
    return conn


@app.context_processor
def utility_processor():
    def convert_epoch_to_date(epoch):
        return datetime.fromtimestamp(epoch).strftime('%Y-%m-%d')

    return dict(convert_time=convert_epoch_to_date)


@app.route('/')
@app.route('/index')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("select * from TestCycle order by lastupdate DESC")
    rows = cur.fetchall()
    conn.close()
    # print(type(rows))
    # print(rows)
    return render_template('index.html', title='Home', rows=rows)


@app.route('/testcycle/<testcycleid>')
def testcycle(testcycleid):
    conn = get_db_connection()
    cur = conn.cursor()
    # query =
    cur.execute("select * from TestCycle where testcycleid=?", [testcycleid])
    row = cur.fetchone()
    # print(row)
    if row is None:
        abort(404)
    cur.execute("select * from Test where testcycleid=? order by lastupdate DESC", [testcycleid])
    test_row = cur.fetchall()
    conn.close()
    return render_template('testpage.html', title='Test Cycle', row=row, test_row=test_row)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title='Home'), 404


@app.route('/test/<testid>')
def test(testid):
    conn = get_db_connection()
    cur = conn.cursor()
    # query =
    cur.execute("select * from Test where testid=?", [testid])
    row = cur.fetchone()
    # print(row)
    if row is None:
        abort(404)
    # print(row['conversationid'])
    conn.close()
    return render_template('testitem.html', title='Test Item', row=row)


@app.route('/createtestcycle', methods=['GET', 'POST'])
def createtestcycle():
    form = TestCycleForm()
    if request.method == 'POST':
        print(form.testcyclename.data)
        # flash('Data from the form: testname {}, testdesc={}'.format(
        #    form.testcyclename.data, form.testcycledesc.data))
        # if form.testcycleimage.data:
        #    filename = secure_filename(form.testcycleimage.data.filename)
        #    print(filename)
        conn = get_db_connection()
        cur = conn.cursor()
        sqlstmt = "insert into TestCycle ('testcyclename','description','project','projectdescription','trellolink','imageurl','createdate','lastupdate') values(?,?,?,?,?,?,?,?);"
        print(sqlstmt)
        filename = secure_filename(form.testcycleimage.data.filename) if form.testcycleimage.data else None
        data_tuple = (form.testcyclename.data,
                      form.testcycledesc.data,
                      form.projectname.data,
                      form.projectdesc.data,
                      form.trellolink.data,
                      filename,
                      int(t.time()),
                      int(t.time()))
        cur.execute(sqlstmt, data_tuple)
        conn.commit()
        last_id = cur.lastrowid
        print(last_id)
        # flash('Data Successfully Inserted with ID {}'.format(last_id))
        # flash('Creating Folder for Test Cycle: {}'.format(last_id))
        target_directory = app.config['TESTCYCLE_PREFIX'] + str(last_id)
        print(target_directory)
        parent_directory = app.static_folder + '/uploads/'
        print(parent_directory)
        mode = 0o777
        path = os.path.join(parent_directory, target_directory)
        try:
            # os.makedirs(path, mode, exist_ok=True)
            os.mkdir(path, mode)
            # flash('Directory Created {}'.format(path))
            if filename:
                form.testcycleimage.data.save(path + '/' + filename)
                filepath = 'uploads/' + app.config['TESTCYCLE_PREFIX'] + str(last_id) + '/' + filename
                cur.execute("update TestCycle set imageurl=?,lasupdate=? where testcycleid=?",
                            [filepath, int(t.time()), last_id])
                conn.commit()
        except OSError as error:
            flash("Directory {} can not be created. Contact Administrator. Error message: {}".format(path, error))
            cur.execute("delete from TestCycle where testcycleid=?", [last_id])
            flash('Test Cycle ID {} removed from database'.format(last_id))
            conn.commit()
            return redirect(url_for('createtestcycle'))
        cur.close()
        conn.close()
        # f = form.testcycleimage.data
        # filename = secure_filename(f.filename)
        # flash('Redirecting to Home Page')
        # time.sleep(5)

        return redirect(url_for('index'))
    return render_template('createtestcycle.html', title='Create Test Cycle', form=form)


@app.route('/testcycle/<testcycleid>/createtestitem', methods=['GET', 'POST'])
def createtestitem(testcycleid):
    form = TestItemForm()
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from TestCycle where testcycleid=?", [testcycleid])
        row = cur.fetchone()
        print(row['testcycleid'])
        if row is None:
            return redirect(url_for('index'))
        conversationid = None
        filename = secure_filename(form.testvideo.data.filename) if form.testvideo.data else None
        sqlstmt = "insert into Test ('testname','testdescription','testcycleid','lastupdate','createdate','testvideourl','conversationid') values(?,?,?,?,?,?,?);"
        data_tuple = (form.testitemname.data,
                      form.testitemdesc.data,
                      row['testcycleid'],
                      int(t.time()),
                      int(t.time()),
                      filename,
                      conversationid)
        cur.execute(sqlstmt, data_tuple)
        conn.commit()
        last_id = cur.lastrowid
        print(last_id)
        target_directory = app.config['TESTITEM_PREFIX'] + str(last_id)
        print(target_directory)
        parent_directory = app.static_folder + '/uploads/'
        print(parent_directory)
        mode = 0o777
        path = os.path.join(parent_directory, target_directory)
        try:
            # os.makedirs(path, mode, exist_ok=True)
            os.mkdir(path, mode)
            # flash('Directory Created {}'.format(path))
            if filename:
                form.testvideo.data.save(path + '/' + filename)
                filepath = 'uploads/' + app.config['TESTITEM_PREFIX'] + str(last_id) + '/' + filename
                cur.execute("update Test set testvideourl=?,lastupdate=? where testid=?",
                            [filepath, int(t.time()), last_id])
                conn.commit()
        except OSError as error:
            flash("Directory {} can not be created. Contact Administrator. Error message: {}".format(path, error))
            cur.execute("delete from Test where testid=?", [last_id])
            flash('Test Item ID {} removed from database'.format(last_id))
            conn.commit()
            return redirect(url_for('createtestitem', testcycleid=str(row['testcycleid'])))
        cur.close()
        conn.close()
        return redirect(url_for('testcycle', testcycleid=row['testcycleid']))
    return render_template('createtestitem.html', title='Create Test Item', form=form)


@app.route('/test/<testid>/edittestitem', methods=['GET', 'POST'])
def edittestitem(testid):
    form = TestItemUpdateForm()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("select * from Test where testid=?", [testid])
    row = cur.fetchone()
    if form.validate_on_submit():
        filename = secure_filename(form.testvideo.data.filename) if form.testvideo.data else None
        print(filename)
        cur.execute("update Test set testname=?, testdescription=?, lastupdate=? where testid=?",
                    [form.testitemname.data, form.testitemdesc.data, int(t.time()), row['testid']])
        conn.commit()
        if filename:
            target_directory = app.config['TESTITEM_PREFIX'] + str(row['testid'])
            print(target_directory)
            parent_directory = app.static_folder + '/uploads/'
            print(parent_directory)
            path = os.path.join(parent_directory, target_directory)
            mode = 0o777
            if not os.path.isdir(path):
                os.makedirs(path, mode, exist_ok=True)
            form.testvideo.data.save(path + '/' + filename)
            filepath = 'uploads/' + app.config['TESTITEM_PREFIX'] + str(row['testid']) + '/' + filename
            conversationid = None
            cur.execute("update Test set testvideourl=?,lastupdate=?,conversationid=? where testid=?",
                        [filepath, int(t.time()), conversationid, row['testid']])
            conn.commit()
        # flash('Your changes have been saved.')
        return redirect(url_for('test', testid=testid))
    elif request.method == 'GET':
        if row is None:
            return redirect('index')
        form.testitemname.data = row['testname']
        form.testitemdesc.data = row['testdescription']
        form.testvideo.data = row['testvideourl']
    cur.close()
    conn.close()
    return render_template('edit_test_item.html', title='Edit Test Item', form=form)


@app.route('/testcycle/<testcycleid>/edittestcycle', methods=['GET', 'POST'])
def edittestcycle(testcycleid):
    form = TestCycleUpdateForm()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("select * from TestCycle where testcycleid=?", [testcycleid])
    row = cur.fetchone()
    if form.validate_on_submit():
        filename = secure_filename(form.testcycleimage.data.filename) if form.testcycleimage.data else None
        # print(filename)
        cur.execute(
            "update TestCycle set testcyclename=?, description=?, project=?, projectdescription=?, trellolink=?, lastupdate=? where testcycleid=?",
            [form.testcyclename.data, form.testcycledesc.data, form.projectname.data, form.projectdesc.data,
             form.trellolink.data, int(t.time()), row['testcycleid']])
        conn.commit()
        if filename:
            target_directory = app.config['TESTCYCLE_PREFIX'] + str(row['testcycleid'])
            print(target_directory)
            parent_directory = app.static_folder + '/uploads/'
            print(parent_directory)
            path = os.path.join(parent_directory, target_directory)
            mode = 0o777
            if not os.path.isdir(path):
                os.makedirs(path, mode, exist_ok=True)
            form.testcycleimage.data.save(path + '/' + filename)
            filepath = 'uploads/' + app.config['TESTCYCLE_PREFIX'] + str(row['testcycleid']) + '/' + filename
            cur.execute("update TestCycle set imageurl=?,lastupdate=? where testcycleid=?",
                        [filepath, int(t.time()), row['testcycleid']])
            conn.commit()
        # flash('Your changes have been saved.')
        return redirect(url_for('testcycle', testcycleid=testcycleid))
    elif request.method == 'GET':
        if row is None:
            return redirect('index')
        form.testcyclename.data = row['testcyclename']
        form.testcycledesc.data = row['description']
        form.projectname.data = row['project']
        form.projectdesc.data = row['projectdescription']
        form.trellolink.data = row['trellolink']
        form.testcycleimage.data = row['imageurl']
    cur.close()
    conn.close()
    return render_template('edit_test_cycle.html', title='Edit Test Cycle', form=form)


@app.route('/generatedata', methods=['GET', 'POST'])
def generatedata():
    # print(url_for('static'))
    print(request.form['data'])
    print(request.form['generate_data'])
    # print(request.args.get('testid'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("select * from Test where testid=?", [request.form['data']])
    row = cur.fetchone()
    print(row['testvideourl'])
    print(row['conversationid'])
    if request.method == 'POST':
        if row['conversationid'] is None or request.form['generate_data'] == 'true':
            # print()
            target_directory = app.config['TESTITEM_PREFIX'] + str(row['testid']) + '/'
            # print(target_directory)
            parent_directory = app.static_folder + '/uploads/'
            # print(parent_directory)
            path = os.path.join(parent_directory, target_directory, row['testvideourl'].split('/')[-1])
            print(path)
            # path = app.static_folder + '\\uploads\\' + app.config['TESTITEM_PREFIX'] + request.form[
            #    'data'] + '\\' + 'Telegram.mp4'
            local_path = r'{}'.format(path)
            conversation_object = symbl.Video.process_file(
                file_path=local_path
            )
            conv_id = conversation_object.get_conversation_id()
            cur.execute("update Test set conversationid=?,lastupdate=? where testid=?",
                        [conv_id, int(t.time()), row['testid']])
            conn.commit()
            message_list = json.loads(to_json(conversation_object.get_messages().messages))
            topics_list = json.loads(to_json(conversation_object.get_topics().topics))
            action_items = json.loads(to_json(conversation_object.get_action_items().action_items))
            follow_ups = json.loads(to_json(conversation_object.get_follow_ups().follow_ups))
            questions = json.loads(to_json(conversation_object.get_questions().questions))

        else:
            # pass
            message_list = symbl.Conversations.get_messages(conversation_id=row['conversationid'])
            topics_list = symbl.Conversations.get_topics(conversation_id=row['conversationid'])
            # print(message_list)
            follow_ups = symbl.Conversations.get_follow_ups(conversation_id=row['conversationid'])
            action_items = symbl.Conversations.get_action_items(conversation_id=row['conversationid'])
            questions = symbl.Conversations.get_questions(conversation_id=row['conversationid'])
            message_list = json.loads(to_json(message_list.messages))
            topics_list = json.loads(to_json(topics_list.topics))
            action_items = json.loads(to_json(action_items.action_items))
            follow_ups = json.loads(to_json(follow_ups.follow_ups))
            questions = json.loads(to_json(questions.questions))

    # print(message_list)
    # print(topics_list)
    cur.close()
    conn.close()
    return jsonify({'messages': message_list, 'topics': topics_list, 'actions': action_items, 'follow_ups': follow_ups,
                    'questions': questions})


@app.route('/trelloexport', methods=['GET', 'POST'])
def trelloexport():
    if request.method == 'POST':
        client = TrelloClient(app.config['TRELLO_API'], app.config['TRELLO_TOKEN'])
        # print(request.form['data'])
        board = client.get_board(app.config['BOARD_ID'])
        target_list = board.get_list(app.config['LIST_ID'])
        print(board)
        print(target_list)
        print(json.loads(request.form['data']))
        for item in json.loads(request.form['data']):
            print(item)
            card_desc = "Trello cards are your portal to more organized work—where every " \
                        "single part of your task can be managed, " \
                        "tracked, and shared with teammates. Open any card to uncover " \
                        "an ecosystem of checklists, due dates, attachments, " \
                        "conversations, and more."
            card_name = item
            create_card = target_list.add_card(card_name, card_desc)
        message = "Cards created successfully on Board {} and Lane {}".format(board.name, target_list.name)

    return jsonify({'message': message})


if __name__ == "__main__":
    app.run(debug=True)

