from flask import Flask, redirect, url_for, render_template, request, get_flashed_messages, flash
from models import db, User, ToDO
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, current_user, login_user
import datetime

# Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = '\x14B~^\x07\xe1\x197\xda\x18\xa6[[\x05\x03QVg\xce%\xb2<\x80\xa4\x00'
app.config['DEBUG'] = True

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

db.create_all()

#Auth
login_manager = LoginManager()
login_manager.login_view = 'loginPage'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user):
    return User.query.get(user)

def get_current_user():
    return current_user

#Access decorator
def unauthenticated_user(view_func):
    def wrapper_func(id, *args, **kwargs):
        if not current_user.todo_items.filter_by(id=id):
            return redirect('/mytodos')

@app.route("/", methods=['GET'])
@app.route('/home/', methods=['GET'])
def index():
    '''
    Home page
    '''
    if current_user.is_authenticated:
        return redirect('/mytodos')
    return render_template('home.html')

@app.route('/mytodos/', methods=['GET', 'POST'])
@login_required
def todos():
    '''
    ToDo Page
    '''
    if request.method == 'POST':
        todoTitle = request.form.get('todoTitle')
        todoDesc = request.form.get('description')
        completed = request.form.get('completed')
        duedate = datetime.datetime.strptime(request.form.get('duedate'), '%Y-%m-%dT%H:%M')
        if completed == 'on':
            completed = True
        if current_user.todo_items.first():
            order = current_user.todo_items.order_by(ToDO.order_in_queue.desc()).first().order_in_queue + 1
        else:
            order = 0
        new_todo = ToDO(title=todoTitle, description=todoDesc, due_date=duedate, completed=completed, user=current_user, order_in_queue=order)
        db.session.add(new_todo)
        db.session.commit()
        return redirect('/mytodos')
    user_todos = current_user.todo_items.order_by(ToDO.order_in_queue)
    return render_template('todos.html', todos=user_todos)

@app.route('/editTodo/<string:id>/', methods=['GET', 'POST'])
@login_required
def editTodo(id):
    '''
    Edit ToDo page
    '''
    if not current_user.todo_items:
        return redirect('/mytodos')
    elif not current_user.todo_items.filter(ToDO.id == id).first():
        return redirect('/mytodos')

    item = ToDO.query.get(id)
    date = item.due_date
    y = date.year
    m = str(date.month) if len(str(date.month)) == 2 else '0' + str(date.month)
    d = str(date.day) if len(str(date.day)) == 2 else '0' + str(date.day)
    h = str(date.hour) if len(str(date.hour)) == 2 else '0' + str(date.hour)
    minute = str(date.minute) if len(str(date.minute)) == 2 else '0' + str(date.minute)
    date = str(y) + '-' + m + '-' + d + 'T' + h + ':' + minute
    if request.method == 'POST':
        item.title = request.form.get('todoTitle')
        item.description = request.form.get('description')
        completed = request.form.get('completed')
        item.due_date = datetime.datetime.strptime(request.form.get('duedate'), '%Y-%m-%dT%H:%M')
        if completed == 'on':
            completed = True
        item.completed = completed
        db.session.commit()
        return redirect('/mytodos')

    return render_template('editTodo.html', item=item, date=date)

@app.route('/completeTodo/<string:id>/', methods=['GET', 'POST'])
@login_required
def completeTodo(id):
    '''
    Complete ToDo view
    '''
    if not current_user.todo_items:
        return redirect('/mytodos')
    elif not current_user.todo_items.filter(ToDO.id == id).first():
        return redirect('/mytodos')

    item = ToDO.query.get(id)
    c = not item.completed
    item.completed = c
    db.session.commit()
    return redirect('/mytodos')

@app.route('/moveTodo/<string:id>/<string:direction>/', methods=['GET', 'POST'])
@login_required
def moveTodo(id, direction):
    '''
    Moves ToDo's orders
    '''
    if not current_user.todo_items:
        return redirect('/mytodos')
    elif not current_user.todo_items.filter(ToDO.id == id).first():
        return redirect('/mytodos')

    item = ToDO.query.get(id)
    items = current_user.todo_items.order_by(ToDO.order_in_queue)
    for ind, i in enumerate(items):
        if i == item:
            break
    
    item_place = item.order_in_queue
    #Four cases
    #Up and item is first
    if direction == 'up' and item == items[0]:
        return redirect('/mytodos')
    #Up and item is not first
    elif direction == 'up':
        switch_item = items[ind-1]
        q = switch_item.order_in_queue
        item.order_in_queue = q
        switch_item.order_in_queue = item_place
    #Down and item is last
    elif direction == 'down' and item == items[-1]:
        return redirect('/mytodos')
    #Down and item is not last
    else:
        switch_item = items[ind+1]
        q = switch_item.order_in_queue
        item.order_in_queue = q
        switch_item.order_in_queue = item_place
    
    db.session.commit()
    return redirect('/mytodos')


@app.route('/delTodo/<string:id>/', methods=['GET', 'DELETE'])
@login_required
def delTodo(id):
    '''
    Delete ToDo view
    '''
    if not current_user.todo_items:
        return redirect('/mytodos')
    elif not current_user.todo_items.filter(ToDO.id == id).first():
        return redirect('/mytodos')
    item = ToDO.query.get(id)
    db.session.delete(item)
    db.session.commit()
    return redirect('/mytodos')

@app.route('/login/', methods=['GET', 'POST'])
def loginPage():
    '''
    Login Page
    '''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True, force=True)
                return redirect('/mytodos')
            else:
                flash('Password incorrect', category='error')
        else:
            flash("User doesn't exist", category='error')
    return render_template('login.html')

@app.route('/signup/', methods=['GET', 'POST'])
def signupPage():
    '''
    Sign Up Page
    '''
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        p1 = request.form.get('password1')
        p2 = request.form.get('password2')
        email_unique = User.query.filter_by(email=email).first()
        if email_unique:
            flash('Email is already associated with an account', category='error')
        elif p1 != p2:
            flash('Passwords do not match', category='error')
        else:
            new_user = User(fullname=fullname, email=email, password=generate_password_hash(p1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('User successfully created!', category='success')
            return redirect('/login')
    return render_template('signup.html')

@login_required
@app.route('/logout/', methods=['GET'])
def logout():
    logout_user()
    return redirect('/home')

if __name__ == "__main__":
    app.run(port=3000)