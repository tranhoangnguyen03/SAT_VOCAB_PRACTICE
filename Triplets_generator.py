import os, requests, re, time, datetime, pandas_gbq, getpass, json, IPython, uuid, google.cloud.storage
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
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
    sentence = input('''Type here --> ''')
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
    url = f'https://www.google.com/search?hl=en&q={word}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content).find("div", class_= "VpH2eb vmod XpoqFe")
    if not soup:
      print(word,'Google Fails') 
      url = f'https://wordsapiv1.p.mashape.com/words/{word}'
      headers = {'x-rapidapi-host': "wordsapiv1.p.rapidapi.com",
                 'x-rapidapi-key': "949abd3c54msh638191acd9c73abp1b45abjsn596b27b8d9b7"}
      response = requests.get(url, headers=headers)
      json_ = response.json()
      val = [len(v['synonyms'])for i,v in enumerate(json_['results']) if 'synonyms' in v]
      if len(val)>0 : val = json_['results'][val.index(max(val))]
      else: val = json_['results'][0]
      synonyms = None
      example = None
      if 'examples' in val: example = val['examples'][0].replace(word,f'{self.format.GREEN}{word}{self.format.RESET}')
      if 'synonyms' in val: synonyms = val['synonyms']
      return {'Word': word, 'Form': val['partOfSpeech'], 'Definition': val['definition'],
              'Synonyms': synonyms, 'Example': example}
    else:
      print(word,'Google No Fails') 
      form = soup.find(class_='vpx4Fd').find(class_='pgRvse vdBwhd').getText()
      span = [i.getText() for i in soup.find(class_='thODed Uekwlc XpoqFe').find_all('span') if len(i.getText())>1]
      definition = [i for i in span if " " in i][0]
      synonyms = [i for i in span if " " not in i][0:5]
      example = soup.find(class_='thODed Uekwlc XpoqFe').find(class_='vk_gy')
      if not example: example = ' '
      else: example = example.getText().replace('"','').replace(word,f'{self.format.GREEN}{word}{self.format.RESET}')
      return {'Word': word, 'Form': form, 'Definition': definition,
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
