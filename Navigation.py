import os, requests, re, time, datetime, pandas_gbq, getpass
import numpy as np
from google.oauth2 import service_account
import pandas as pd
from IPython.display import clear_output

class Navigation_simple:
  def __init__(self, Engine):
    self.Engine = Engine
    self.credentials = service_account.Credentials.from_service_account_file('key.json')
    self.existing_credentials = pd.read_gbq("""SELECT USERNAME, PASSWORD FROM SAT_VOCAB_PROJECT.LOGIN_CREDENTIALS""", project_id="mysandbox-233913", credentials= self.credentials)
    self.dict_creds = {row[1].USERNAME:row[1].PASSWORD for row in self.existing_credentials.iterrows()}
    self.username = None

    self.flag_valid_login = False

    self.reminder_message = '''
********************************************************
REMINDER: YOU CAN TYPE DONE or QUIT to exit the program
********************************************************
'''

  def check_username(self, username):
    if not username.isalnum():
      raise ValueError('Sorry, UserName only accepts A-Z, a-z, and numbers..')
    if not len(username)>=5:
      raise ValueError('Ahh, we do not accept UserName with length below 5')
    if username in self.existing_credentials.USERNAME.values.tolist(): 
      return True
    else: return False
  
  def check_password(self, username, password):
    if self.dict_creds[username] == password: return True
    else: return False

  def Start(self, username, LoginOrCreateNew):
    check_existing_username = self.check_username(username)
    if LoginOrCreateNew == "Login":
      if check_existing_username:
        print('please input password ->',end='')
        password = getpass.getpass()
        if self.check_password(username, password):
          self.username = username
          self.flag_valid_login = True        
          timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
          user_log = pd.DataFrame({'USER':self.username,'ACTIVITY':'LOGIN','TIMESTAMP':timestamp}, index=[0])
          user_log.TIMESTAMP = pd.to_datetime(user_log.TIMESTAMP)
          pandas_gbq.to_gbq(user_log, 'SAT_VOCAB_PROJECT.USER_LOG', project_id="mysandbox-233913", credentials=self.credentials, if_exists = 'append')
          self.success('Login Success!')
          print('''
--------------------------------------------------------------------------------
                    Practice or Test your vocabs below!''')            
        else: 
          print('Password incorrect!')
          print('''
--------------------------------------------------------------------------------
                            Please try again!''')   
      else: 
        print('UserName not found!') 
        print('''
--------------------------------------------------------------------------------
              Please try again with another UserName!''')  
    
    if LoginOrCreateNew == "Create_New_Account":
      if check_existing_username:
        print('UserName already exists!')
        print('''
--------------------------------------------------------------------------------
              Please try again with another UserName!''') 
      else:
        print('please input password ->',end='')
        password = getpass.getpass()
        print('plz, password again --->',end='')
        password_2 = getpass.getpass()
        if password != password_2:
          print('Passwords do NOT match!')
          print('''
--------------------------------------------------------------------------------
                            Please try again!''') 
        else:
          timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
          credential_log = pd.DataFrame({'ID':self.existing_credentials.ID.max()+1,'USERNAME':username,'PASSWORD':password}, index=[0])
          user_log = pd.DataFrame({'USER':self.username,'ACTIVITY':'CREATE_USER','TIMESTAMP':timestamp}, index=[0])
          user_log.TIMESTAMP = pd.to_datetime(user_log.TIMESTAMP)
          credential_log.to_gbq('SAT_VOCAB_PROJECT.LOGIN_CREDENTIALS', project_id="mysandbox-233913", credentials=self.credentials, if_exists = 'append')
          user_log.to_gbq('SAT_VOCAB_PROJECT.USER_LOG', project_id="mysandbox-233913", credentials=self.credentials, if_exists = 'append')
          self.existing_credentials = pd.read_gbq("""SELECT USERNAME, PASSWORD FROM SAT_VOCAB_PROJECT.LOGIN_CREDENTIALS""", project_id="mysandbox-233913", credentials= self.credentials)
          self.dict_creds = {row[1].USERNAME:row[1].PASSWORD for row in self.existing_credentials.iterrows()}
          self.success('Account successfully created!')
          print('''
--------------------------------------------------------------------------------
              Please login with your newly created account!''')

  def Run(self, PracticeOrTest):
    if self.username == None: print('Please Login!')
    else:
      start = time.time()
      if PracticeOrTest == 'Export':
        clear_output()
        print('FULL WORD LIST BELOW:\n')
        self.Engine.Export()
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        user_log = pd.DataFrame({'USER' : [self.username],
                                'ACTIVITY' : [PracticeOrTest.upper()],
                                'TIMESTAMP' : [timestamp],
                                'WORD' : [None],
                                'SENTENCE' : [None],
                                'SCORE' : [None],
                                'VOCAB_FILE' : [self.Engine.vocab_file],
                                'ACTIVITY_DURATION': [int(time.time()-start)]})
      else:
        assert PracticeOrTest in ['Practice', 'Test'], f'Oi, {self.username}, me no understand your request'
        if not self.flag_valid_login: self.username = 'AdminTest'
        clear_output()
        sentences = {}
        while True:
          clear_output()
          print(self.reminder_message)
          if PracticeOrTest == 'Practice': 
            words, sentence, points, flag_exit = self.Engine.Practice()
          if PracticeOrTest == 'Test': 
            words, sentence, points, flag_exit = self.Engine.Test()
          if flag_exit == True: break
          sentences[sentence] = (', '.join(words), points)
        print(f'''
      ****************************************************************************
      Your total results:''')
        for i,v in sentences.items(): print(v, i)
        ##### Logging acitivities

        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        num_rows = len(sentences)
        user_log = pd.DataFrame({'USER' : [self.username]*num_rows,
                                'ACTIVITY' : [PracticeOrTest.upper()]*num_rows,
                                'TIMESTAMP' : [timestamp]*num_rows,
                                'WORD' : [i[0] for i in sentences.values()],
                                'SENTENCE' : list(sentences.keys()),
                                'SCORE' : [i[1] for i in sentences.values()],
                                'VOCAB_FILE' : [self.Engine.vocab_file]*num_rows,
                                'ACTIVITY_DURATION': [int(time.time()-start)]*num_rows })
        user_log = user_log.astype({'USER': str,
                                    'ACTIVITY': str,
                                    'TIMESTAMP': 'datetime64[ns]',
                                    'WORD': str,
                                    'SENTENCE': str,
                                    'SCORE': int,
                                    'VOCAB_FILE': str,
                                    'ACTIVITY_DURATION': int})
        user_log.to_gbq('SAT_VOCAB_PROJECT.USER_LOG', project_id="mysandbox-233913", credentials=self.credentials, if_exists = 'append')
        self.success('Your Practice Results Have Been Uploaded!')
        print(f'\nThanks for playing {self.username}')

  def success(self, message):
    for i in range(3):
      print(f'\r\\0/\\0/\\0/-{message}-\\0/\\0/\\0/',end='')
      time.sleep(0.5)
      print(f'\r/0\/0\/0\-{message}-/0\/0\/0\\',end='')
      time.sleep(0.5)
      print(f'\r\\0/\\0/\\0/-{message}-\\0/\\0/\\0/',end='')

class ReceiveInput(object):
  def __init__(self, title, callback):
    self._title = title
    self._callback = callback

  def _repr_html_(self):
    callback_id = 'button-' + str(uuid.uuid4())
    output.register_callback(callback_id, self._callback)

    template = """{title}
      <input type="text" id={callback_id} value="ex: 1-405" name={title}></input>
        <script>
          document.querySelector("#{callback_id}").onchange = (e) => {{
            google.colab.kernel.invokeFunction('{callback_id}', [e.target.value], {{}})
            e.preventDefault();
          }};
        </script>"""
    html = template.format(title=self._title, callback_id=callback_id)
    return html 

class SelectOption(object):
  def __init__(self, title, callback, options):
    self._title = title
    self._callback = callback
    self.options = ''' 
'''.join([f'<option value= "{i}"> {i}'for i in options])

  def _repr_html_(self):
    callback_id = 'button-' + str(uuid.uuid4())
    output.register_callback(callback_id, self._callback)

    template = """{title}
    <select id={callback_id}>
"""+self.options+"""
    </select>
        <script>
          document.querySelector("#{callback_id}").onchange = (e) => {{
            google.colab.kernel.invokeFunction('{callback_id}', [e.target.value], {{}})
            e.preventDefault();
          }};
        </script>"""
    html = template.format(title=self._title, callback_id=callback_id)
    return html
