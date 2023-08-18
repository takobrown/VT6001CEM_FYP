import os
import global_var
import dash    
from dash import dcc
from dash import html
from dash import dash_table
import pandas as pd
from dash.dependencies import Input, Output,State
from sqlalchemy import create_engine
import plotly.graph_objects as go
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
engine = create_engine(('mysql+mysqlconnector://flask:Admin123456#@175.178.10.95:3306/RFID'), echo=True,
                       encoding='utf-8')
external_css = [
    "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css"
]
app = dash.Dash(__name__, external_stylesheets=external_css)
app.title = "Pet Monitoring System"
app.config.suppress_callback_exceptions = True
server = app.server
server.config.update(SECRET_KEY=os.urandom(12))
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

infotable = "petinfo"
pettable = "petmanage"
statetable = "petstate"
statisticstable = "petstatistics"
usertable = "users"

info = pd.read_sql(infotable, con=engine)
pet = pd.read_sql(pettable, con=engine)
data = pd.read_sql(statetable, con=engine)
statisticsdata = pd.read_sql(statisticstable, con=engine)
user = pd.read_sql(statetable, con=engine)

class Users(UserMixin, global_var.Users):
    pass

head = html.Div([
    html.Span("Pet Monitoring System")
], style={'display': 'block', 'text-align': 'center', 'font-size': '24px', 'font-weight': 'bold'},className="row header")

def indicator(text, id_value):
    return html.Div([
    html.P(text, style={'display': 'block', 'text-align': 'center', 'font-size': '16px', 'font-weight': 'bold'},className="twelve columns indicator_text"),
    html.P(id=id_value, style={'display': 'block', 'text-align': 'center', 'font-size': '16px'},className="indicator_value"),
], className="col indicator")

columns = info.columns[1:]
col_name = ['Recently Entered Pet', 'Recently Left Pet', 'Max Pet Allowance','Pet with Microchip', 'No. of Occupy', 'No. of Vacancy']
infos = html.Div([
    indicator(col_name[i], col) for i, col in enumerate(columns)
], className='row')
labels = ['Occupy','Vacancy']
print(info)
values = []
values.append((int(info['InPetNums'][0])))
values.append((int(info['OutPetNums'][0])))
piechart = html.Div([
    dcc.Graph(
        id='pet-pie-graph',
        figure={
            'data': [
                    go.Pie(
                    labels=labels,
                    values=values,
                    hole=.3
                )
            ],
            'layout': {
                'title': "Pet Garden Capacity",
            }
        }
    )
])
dateselect = html.Div([
    dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed='2023-01-01',
            max_date_allowed='2026-12-31',
            initial_visible_month='2023-01-01',
            start_date='2023-01-01',
            end_date='2023-12-31',
        ),
        html.Br(),
        html.Button('Submit', id='submit-button')
])

table = html.Div([
    dash_table.DataTable(
        id='datatable',
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True} for i in data.columns[1:]
        ],
        data=data.to_dict('records'),
        editable=True,
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 10,
    ),
])
petlist = list(pet["Name"])
dropDown = html.Div([
    html.Div([
        dcc.Dropdown(id='pet-dropdown',
                 options=[{'label': petlist[i], 'value': item} for i, item in enumerate(petlist)],
                 value=petlist[0], style={'width': '40%'})
        ], className='col-6', style={'padding': '2px', 'margin': '0px 5px 0px'}),
    html.Div(id='choice',style={'font-size': '16px', 'font-weight': 'bold'})
], className='row')

state = data.loc[data['Name']==petlist[0],['Updatetime','State']]
chart = html.Div([
    dcc.Graph(
        id='pet-graph',
        figure={
            'data': [
                {'x': state['Updatetime'], 'y': state['State'], 'type': 'line', 'name': 'State'},
            ],
            'layout': {
                'title': petlist[0] + ' - In & Out Record',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'State'}
            }
        }
    )
])

print(statisticsdata)
statisticschart = html.Div([
    dcc.Graph(
        id='statistics-graph',
        figure={
            'data': [
                {'x': statisticsdata['Updatetime'], 'y': statisticsdata['InPetCounts'], 'type': 'line', 'name': 'In Counts'},
                {'x': statisticsdata['Updatetime'], 'y': statisticsdata['OutPetCounts'], 'type': 'line', 'name': 'Out Counts'},
            ],
            'layout': {
                'title': 'Statistic of Pet Garden Usage',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Counts'}
            }
        }
    )
])

adminlayout = html.Div([
    dcc.Location(id='url_admin', refresh=True),
    dcc.Interval(id="infotimer", interval=1000*60, n_intervals=0),
    dcc.Interval(id="datatimer", interval=1000*60, n_intervals=0),
    dcc.Interval(id="statisticstimer", interval=1000*60*10, n_intervals=0),
    html.Div(id="load_pet_info", style={"display": "none"},),
    head,
    html.Div([
        html.Br(),
        html.Button(id='adminback-button', children='Go back', n_clicks=0),
        infos,
        piechart,
        statisticschart,
        dropDown,
        chart,
        dateselect,
        table,
    ], style={'margin': '0% 30px'}),
])

userlayout = html.Div([
    dcc.Location(id='url_user', refresh=True),
    dcc.Interval(id="infotimer", interval=1000*60, n_intervals=0),
    dcc.Interval(id="datatimer", interval=1000*60, n_intervals=0),
    html.Div(id="load_pet_info", style={"display": "none"},),
    head,
    html.Div([
        html.Br(),
        html.Button(id='userback-button', children='Go back', n_clicks=0),
        infos,
        piechart,
    ], style={'margin': '0% 30px'}),
])
@app.callback(Output('load_pet_info', 'children'), [Input("infotimer", "n_intervals")])
def load_pet_info(n):
    try:
        df = pd.read_sql(infotable, con=engine)
        return df.to_json()
    except:
        pass
def update_info(col):
    def get_data(json, n):
        df = pd.read_json(json)
        return df[col][0]
    return get_data
for col in columns:
    app.callback(Output(col, "children"),
                 [Input('load_pet_info', 'children'), Input("infotimer", "n_intervals")]
     )(update_info(col))
@app.callback(
    Output('pet-pie-graph', 'figure'),[Input("datatimer", "n_intervals")])    
def update_pie(n):
    data = pd.read_sql(infotable, con=engine)
    values = []
    values.append((int(data['InPetNums'][0])))
    values.append((int(data['OutPetNums'][0])))
    fig = {
            'data': [
                    go.Pie(
                    labels=labels,
                    values=values,
                    hole=.3
                )
            ],
            'layout': {
                'title': "Pet Garden Capacity",
            }
    }
    return fig
@app.callback(
    Output('datatable', 'data'),
    [Input('submit-button', 'n_clicks'),Input("datatimer", "n_intervals"),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_table(n_clicks,n,start_date='2023-01-01', end_date='2023-12-31'):
    df = pd.read_sql(statetable, engine)
    filtered_df = df[(df['Updatetime'] >= start_date) & (df['Updatetime'] <= end_date)]
    return filtered_df.to_dict('records')
@app.callback(
    Output('choice', 'children'),[Input('pet-dropdown', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)
@app.callback(
    Output('pet-graph', 'figure'),[Input("datatimer", "n_intervals"),Input('pet-dropdown', 'value')])
def update_figure(n,selected):
    data = pd.read_sql(statetable, con=engine)
    state = data.loc[data['Name']==selected]
    fig = {
            'data': [
                {'x': state['Updatetime'], 'y': state['State'], 'type': 'line', 'name': 'State'},
            ],
            'layout': {
                'title': selected + ' - In & Out Record',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'State'}
            }
        }
    return fig
@app.callback(
    Output('statistics-graph', 'figure'),Input("statisticstimer", "n_intervals"))
def update_statistics(n):
    global_var.petStatisticsUpdate()
    data = pd.read_sql(statisticstable, con=engine)
    fig = {
        'data': [
            {'x': data['Updatetime'], 'y': data['InPetCounts'], 'type': 'line', 'name': 'In Counts'},
            {'x': data['Updatetime'], 'y': data['OutPetCounts'], 'type': 'line', 'name': 'Out Counts'},
        ],
        'layout': {
            'title': 'Statistic of Pet Garden Usage',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Counts'}
        }
    }
    return fig
create = html.Div([ html.H1('Create User Account')
        , dcc.Location(id='create_user', refresh=True)
        , dcc.Input(id="username"
            , type="text"
            , placeholder="user name"
            , maxLength =30)
        , dcc.Input(id="password"
            , type="password"
            , placeholder="password")
        , dcc.Input(id="usertype"
            , type="text"
            , placeholder="user type"
            , maxLength = 30)
        , html.Button('Create User', id='submit-val', n_clicks=0)
        , html.Div(id='container-button-basic')
    ])
login =  html.Div([dcc.Location(id='url_login', refresh=True)
            , html.H2('''Please log in to continue:''', id='h1')
            , dcc.Input(placeholder='Enter your username',
                    type='text',
                    id='uname-box')
            , dcc.Input(placeholder='Enter your password',
                    type='password',
                    id='pwd-box')
            , html.Button(children='Login',
                    n_clicks=0,
                    type='submit',
                    id='login-button')
            , html.Div(children='', id='output-state')
        ])
failed = html.Div([ dcc.Location(id='url_login_df', refresh=True)
            , html.Div([html.H2('Log in Failed. Please try again.')
                    , html.Br()
                    , html.Div([login])
                    , html.Br()
                    , html.Button(id='failedback-button', children='Go back', n_clicks=0)
                ])
        ])
other = html.Div([ dcc.Location(id='url_login_error', refresh=True)
            , html.Div([html.H2('User type Error. Please try again.')
                    , html.Br()
                    , html.Div([login])
                    , html.Br()
                    , html.Button(id='otherback-button', children='Go back', n_clicks=0)
                ])
        ])
logout = html.Div([dcc.Location(id='logout', refresh=True)
        , html.Br()
        , html.Div(html.H2('You have been logged out - Please login'))
        , html.Br()
        , html.Div([login])
        , html.Button(id='logoutback-button', children='Go back', n_clicks=0)
    ])
app.layout= html.Div([
            html.Div(id='page-content', className='content')
            ,  dcc.Location(id='url', refresh=False)
        ])
@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    session = global_var.Session()
    session.flush()
    user = session.query(Users).filter(Users.id == user_id).first()
    session.close()
    print(user)
    return user
@app.callback(
    Output('page-content', 'children')
    , [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return create
    elif pathname == '/login':
        return login
    elif pathname == '/success':
        if current_user.is_authenticated:
            if current_user.usertype == 'admin':
                return adminlayout
            elif current_user.usertype == 'user':
                return userlayout
            else:
                return other
        else:
            return failed
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return logout
        else:
            return logout
    else:
        return '404'
@app.callback(
   [Output('container-button-basic', "children")]
    , [Input('submit-val', 'n_clicks')]
    , [State('username', 'value'), State('password', 'value'), State('usertype', 'value')])
def insert_users(n_clicks, un, pw, ty):
    if un is not None and pw is not None and ty is not None:
        session = global_var.Session()
        try:
            session.flush()
            item = Users(username=un, password=pw,usertype=ty)
            session.add(item)
            session.commit()
        except Exception as e:
            print(e)
            print("Add Fail")
            session.rollback()
        finally:
            session.close()
        return [login]
    else:
        return [html.Div([html.H2('Already have a user account?'), dcc.Link('Click here to Log In', href='/login')])]
@app.callback(
    Output('url_login', 'pathname')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def successful(n_clicks, input1, input2):
    session = global_var.Session()
    session.flush()
    user = session.query(Users).filter(Users.username == input1).first()
    session.close()
    if user:
        if user.password == input2:
            login_user(user)
            return '/success'
        else:
            pass
    else:
        pass
@app.callback(
    Output('output-state', 'children')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def update_output(n_clicks, input1, input2):
    if n_clicks > 0:
        session = global_var.Session()
        session.flush()
        user = session.query(Users).filter(Users.username == input1).first()
        session.close()
        if user:
            if user.password == input2:
                return ''
            else:
                return 'Incorrect username or password'
        else:
            return 'Incorrect username or password'
    else:
        return ''
@app.callback(
    Output('url_admin', 'pathname')
    , [Input('adminback-button', 'n_clicks')])
def admin_dashboard(n_clicks):
    print(n_clicks)
    if n_clicks > 0:
        return '/'
@app.callback(
    Output('url_user', 'pathname')
    , [Input('userback-button', 'n_clicks')])
def user_dashboard(n_clicks):
    print(n_clicks)
    if n_clicks > 0:
        return '/'
@app.callback(
    Output('url_login_df', 'pathname')
    , [Input('failedback-button', 'n_clicks')])
def failed_dashboard(n_clicks):
    print(n_clicks)
    if n_clicks > 0:
        return '/'
@app.callback(
    Output('url_login_other', 'pathname')
    , [Input('otherback-button', 'n_clicks')])
def other_dashboard(n_clicks):
    print(n_clicks)
    if n_clicks > 0:
        return '/'
@app.callback(
    Output('url_logout', 'pathname')
    , [Input('logoutback-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    print(n_clicks)
    if n_clicks > 0:
        return '/'
    
if __name__ == '__main__':
    #app.run_server(host='0.0.0.0',debug=False, threaded=True, port=5000)
    app.run_server(debug=False, threaded=True, port=5000)