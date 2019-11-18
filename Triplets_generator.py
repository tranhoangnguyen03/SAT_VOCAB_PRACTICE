class MainEngine:
  def __init__(self, vocab_file):
    class _format_:
      GREEN = '\033[92m'
      BOLD = '\033[1m'
      UNDERLINE = '\033[4m'
      RESET = '\033[0m'
    self.format = _format_
    if not os.path.isfile(vocab_file): os.system(f'gsutil cp gs://sat_vocab_test/Vocab_txt/{vocab_file} .')
    assert os.path.isfile(vocab_file), 'Vocab file not found!' 
    with open(vocab_file,'r') as file:
      self.string_ = file.read()
    self.string_ = self.string_.strip('\n').split('''\n\n''')
    self.words_bank = [i[:i.find('-')-1].replace('TO ','').replace('to ','').lower().strip('') for i in self.string_]  
    self.words_bank_test = [i[:i.find(')')+1].replace('TO ','').replace('to ','').lower().strip('') for i in self.string_]
    self.used_triplets = []
    self.used_triplets_test = []
    self.vocab_file = vocab_file

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
              ----------------------""")
    print(f"{self.format.UNDERLINE}{self.format.BOLD}MAKE YOUR SENTENCE:{self.format.RESET}")
    # """
    return None

  def score(self, words, sentence):
    return np.sum([i[:i.find('-')].replace('TO ','').replace('to ','').strip(' ').upper() in sentence.upper() for i in words])
