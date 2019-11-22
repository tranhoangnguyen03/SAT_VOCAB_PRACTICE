import os, requests, re, time, datetime, pandas_gbq, getpass, json, IPython, uuid
import numpy as np
import pandas as pd
from google.oauth2 import service_account
from google.colab import output
from IPython.display import clear_output

class MainEngine:
  def __init__(self, Selection, wordFam):
    class _format_:
      GREEN = '\033[92m'
      BOLD = '\033[1m'
      UNDERLINE = '\033[4m'
      RESET = '\033[0m'
    self.format = _format_
    self.wordFam = wordFam
    self.string_ = Selection.string_.strip('').split('''\n\n''')
    self.vocab_file = Selection.choice
    self.words_bank = [i[:i.find('-')-1].replace('TO ','').replace('to ','').lower().strip('') for i in self.string_]  
    self.words_bank_test = [i[:i.find(')')+1].replace('TO ','').replace('to ','').lower().strip('') for i in self.string_]
    if Selection.from_to != None:
      from_ = Selection.from_to[0]
      to_ = Selection.from_to[1]+1
      self.words_bank = self.words_bank[from_:to_]
      self.words_bank_test = self.words_bank_test[from_:to_]
      self.vocab_file = self.vocab_file+f'_{from_}_{to_}'
    self.used_triplets = []
    self.used_triplets_test = []    

  def Export(self):
    self.present(self.words_bank)

  def Practice(self):
    flag_exit = False
    triplet = self.get_word_triplet()
    _ = self.present(triplet)
    sentence = input('''Type here --> ''')
    if sentence.strip('').upper() in ['DONE','QUIT','EXIT']: flag_exit = True
    points = self.score(triplet, sentence)
    print(f'Your score is {points}\n')
    for i in triplet: sentence = sentence.upper().replace(i.upper(), f'{self.format.BOLD}{self.format.UNDERLINE} {i.upper()} {self.format.RESET}').lower().capitalize() 
    return triplet.tolist(), sentence, points, flag_exit

  def Test(self):
    flag_exit = False
    triplet = self.get_word_triplet_test()
    # """
    print(f"""Your word triplet is {triplet}
  Make your sentence:\n""")
    sentence = input()
    # """
    if sentence.strip('').upper() in ['DONE','QUIT','EXIT']: flag_exit = True
    points = self.score(triplet, sentence)
    print(f'Your score is {points}\n')
    for i in triplet: sentence = sentence.upper().replace(i.upper(), f'{self.format.BOLD}{self.format.UNDERLINE}{i.upper()}{self.format.RESET}').lower().capitalize() 
    return triplet, sentence, points, flag_exit

  def get_word_triplet(self):
    triplet = np.random.choice(self.words_bank, 3, replace=False)
    count = 0
    while set(triplet) in self.used_triplets: 
      count += 1
      triplet = np.random.choice(self.words_bank, 3, replace=False)
      if count >10 : break
    self.used_triplets.append(set(triplet))
    return triplet

  def get_word_triplet_test(self):
    triplet = np.random.choice(self.words_bank_test, 3, replace=False)
    while set(triplet) in self.used_triplets_test: 
      triplet = np.random.choice(self.words_bank_test, 3, replace=False)
    self.used_triplets_test.append(set(triplet))
    return triplet  

  def get_definition(self, word):
    url = f'https://googledictionaryapi.eu-gb.mybluemix.net/?define={word}'
    html = requests.get(url)
    json_ = html.json()
    for i,v in json_[0]['meaning'].items():
      example = None
      synonyms = None
      if 'example' in v[0].keys(): example = v[0]['example'].replace(word,f'{self.format.GREEN}{word}{self.format.RESET}')
      if 'synonyms' in v[0].keys(): synonyms = v[0]['synonyms'][:min(5,len(v[0]['synonyms']))]
      return {'Word': word, 'Form': i, 'Definition': v[0]['definition'],
              'Synonyms': synonyms, 'Example': example}

  def present(self, triplet):
    print(f'{self.format.UNDERLINE}{self.format.BOLD}Your word-triplet{self.format.RESET}:')
    for word in triplet:
      dict_ = self.get_definition(word)
      print(f"""{self.format.BOLD}{dict_['Word'].upper()}{self.format.RESET} ({dict_['Form']}) - {dict_['Definition']}
    EXAMPLE: {dict_['Example']}
    Synonyms: {dict_['Synonyms']}
    Word Families: {sorted(self.wordFam.return_fam(word))}
              ----------------------""")
    print(f"{self.format.UNDERLINE}{self.format.BOLD}MAKE YOUR SENTENCE:{self.format.RESET}")
    # """
    return None

  def score(self, words, sentence):
    words = self.wordFam.flatten([self.wordFam.return_fam(word) for word in words])
    return np.sum([i[:i.find('-')].replace('TO ','').replace('to ','').strip(' ').upper() in sentence.upper() for i in words])

class WordFam:
  def __init__(self,file):
    with open(file,'r') as f:
      self.wf = json.load(f)
  
  def return_fam(self, word):
    return self.flatten([self.wf[i] for i, group in enumerate(self.wf) if word in group])
  
  def flatten(self, S):
    if S == []:
      return S
    if isinstance(S[0], list):
      return self.flatten(S[0]) + self.flatten(S[1:])
    return S[:1] + self.flatten(S[1:])  

class Vocab_select:
  def __init__(self):
    self.files_dict = {i[i.rfind('/')+1:]:i for i in os.popen('gsutil ls gs://sat_vocab_test/Vocab_txt/SAT-400').read().split('\n')[1:-1]}
    self.from_to = None
  
  def GetFiles(self, a):
    output.clear()
    self.choice = a
    os.system(f'gsutil cp {file_dict[a]} .')
    #if not os.path.isfile(a): os.popen(f'gsutil cp {file_dict[a]} .')
    #assert os.path.isfile(a), 'Vocab file not found!'
    with open(a,'r') as file:
      self.string_ = file.read()
    if a != '999_vocab_SAT_ALL.txt':
      print('''
--------------------------------------------------------------------------------
              Vocab file loaded! Please continue below!''')
    else: 
      print('Please input your custom word range:')
      display(ReceiveInput('Input format: [start]-[end]', self.GetCustomFiles))
      print('''
--------------------------------------------------------------------------------
              Vocab file loaded! Please continue below!''')
  
  def GetCustomFiles(self, value):
    output.clear()
    self.from_to = (int(value[:value.find('-')]),int(value[value.find('-')+1:]))
    print(f'Custom Vocab list created from word[{self.from_to[0]}] to word[{self.from_to[1]}]')    
