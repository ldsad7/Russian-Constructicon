# -*- coding: utf-8 -*-

from flask import Flask, render_template, url_for, request, redirect, session
import json
import sys
import re
from time import strftime, gmtime
import urllib
import xml.etree.cElementTree as ET
import os
import numpy as np
from copy import deepcopy
from math import ceil


HREF = "https://svn.spraakdata.gu.se/sb-arkiv/pub/lmf/konstruktikon-rus/konstruktikon-rus.xml"
NAME = 'konstruktikon.xml'
PER_PAGE = 5
app = Flask(__name__)


class Pagination():

    def __init__(self, page, per_page, total_count):
        self.page = int(page)
        self.per_page = int(per_page)
        self.total_count = int(total_count)

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.total_count

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.total_count + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

@app.route('/')
def main_page():
    with open(NAME, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines()):
            if i == 1:
                date = line
                break
    date, time = re.findall("([0-9]{4}-[0-9]{2}-[0-9]{2}).*?([0-9]{2}:[0-9]{2}:[0-9]{2})", date)[0]
    my_date, my_time = strftime("%Y-%m-%d %H:%M:%S", gmtime()).split()
    if my_date > date:
        refresh_file()
    parseXML(NAME)
    with open('data.json', 'r', encoding='utf-8') as f:
        dct = json.load(f)
    date = sorted(np.array(dct['lastmodified'])[:, 0])
    time = sorted(np.array(dct['lastmodified'])[:, 1])
    emails = sorted(list(np.unique(np.array(dct['lastmodifiedBy']))))
    for i, email in enumerate(emails):
        emails[i] = re.sub("(.*?)@.*", r"\1", email)
    cefr = [elem.capitalize() for elem in list(np.unique(np.array(dct['cefr']))) if elem]
    pos = sorted(['Noun', 'AdjP', 'SCONJ', 'NounP', 'Particle', 'VerbP', 'Verb', 'Adj', 'Clause', 'Num', 'Preposition', 'XP', 'PronounP', 'Intj', 'Pronoun', 'NumP', 'Adv', 'Conjunction'])
    roles = sorted(['Actant', 'Action', 'Activity', 'Adverb', 'Agent', 'Assessment', 'Associated', 'Assumption', 'Beneficiary', 'Cause', 'Circumstance', 'Conclusion', 'Condition', 'Container', 'Context', 'Copula', 'Estimation', 'Evaluation', 'Event', 'Event/Action', 'Evidence', 'Experiencer', 'Factor', 'Goal', 'Intensifier', 'Limitation', 'Link', 'Location', 'Number', 'Object', 'Participant', 'Patient', 'Property', 'Protagonist', 'Prototype', 'Purpose', 'Quality', 'Quantity', 'Reason', 'Recipient', 'Referent', 'Result', 'Role', 'Set', 'Situation', 'Source', 'Standard', 'State', 'Stimulus', 'Theme', 'Time', 'Topic'])
    msd = sorted(['Number=Sg', 'Prep=Place', 'Verb=Short', 'Person=3p', 'Adj=Supr', 'Case=Loc', 'Case=Acc', 'Adj=Plen', 'Trans=Tran', 'Case=Abl', 'Mood=Inf', 'Case=Dat', 'Part=Neg', 'Case=Nom', 'Part=Limiting', 'Mood=Imper', 'Tense=Inpraes', 'Adv=Degree', 'Adj=Comp', 'Trans=Intr', 'Verb=Reflexive', 'Tense=Praet', 'Adj=Brev', 'Pron=Interrog', 'Aspect=Pf', 'Mood=Indic', 'Tense=Praes', 'Pron=Neg', 'Gender=n', 'Case=Gen', 'Pron=Personal', 'Person=2p', 'Number=Pl', 'Case=Part', 'Case=Ins', 'Aspect=Ipf', 'Adv=Comp'])
    auxs = sorted(['Animate', 'Facultative', 'Invariable', 'Negative', 'Case=Nom', 'Plural', 'Reflexive', 'Transitive', 'Type=Positive'])
    return render_template('main_page.html', max_date = date[-1], min_date = date[0], max_time = time[-1][:-3], min_time = time[0][:-3], emails = emails, cefr = cefr, pos = map(json.dumps, pos), roles = map(json.dumps, roles), auxs = map(json.dumps, auxs), msd = map(json.dumps, msd))

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/output1', defaults={'page': 1})
@app.route('/output1/page/<page>')
def output1(page):
    search_param = request.args['search_param']
    construction = request.args['construction']
    with open('data.json', 'r', encoding='utf-8') as f:
        dct = json.load(f)
    indices = []
    if search_param == 'name':
        words = construction.split()
    fl = 0
    message = ''
    st = set([i for i in range(len(dct['id']))])
    if search_param == 'cefr':
        level = construction.strip().lower()
        if level == 'all':
            indices = [i for i in range(len(dct['cefr']))]
        elif ',' in level:
            levels = level.split(',')
            levels = [elem.strip().lower() for elem in levels]
            for level in levels:
                if level not in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
                    fl = 1
                    message = 'There is no such a set of levels. Try again!'
                    break
            if fl == 0:
                for i, elem in enumerate(dct['cefr']):
                    if elem in levels:
                        indices.append(i)
        elif level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
            for i, elem in enumerate(dct['cefr']):
                if elem == level:
                    indices.append(i)
        else:
            fl = 1
            message = 'It is not a CEFR level. Try again!'
    elif search_param == 'number':
        number = construction.strip().lower()
        fl = 0
        if number == 'all':
            indices = [i for i in range(len(dct['id']))]
        elif ':' in number:
            inds = number.split(':')
            try:
                left = int(inds[0].strip())
                right = int(inds[1].strip())
                if len(inds) == 3:
                    step = int(inds[2].strip())
                else:
                    step = 1
            except Exception:
                fl = 1
                message = 'There is no such number/s of the constructions in out database. Try again!!!'
            if fl == 0:
                indices = list(range(left-1, right-1, step))
        elif ',' in number:
            numbers = number.split(',')
            try:
                indices = [int(elem.strip()) - 1 for elem in numbers]
            except Exception:
                fl = 1
                message = 'It is not numbers. Try again!'
                
            if fl == 0:
                indices = sorted(set(indices) & st)
            
            if fl == 0 and indices == []:
                fl = 1
                message = 'There is no such number/s of the constructions in out database. Try again!'
        elif number in [str(i+1) for i in range(len(dct['id']))]:
            try:
                indices = [int(number) - 1]
            except Exception:
                fl = 1
                message = 'There is a word instead of a number'
        else:
            fl = 1
            message = 'There is no such number/s of the constructions in out database. Try again!'
    elif search_param == 'name':
        words = construction.strip('.?!').lower()
        if words == 'all':
            indices = [i for i in range(len(dct['cefr']))]
        else:
            for symbol in '(),–':
                words = words.replace(symbol, '')
            words = ' '.join(words.split('/'))
            words = ' '.join(words.split('|')).split()
            
            maxmax = 0
            indices = [0]
            for i, elem in enumerate(dct['names']):
                num = 0
                for word in words:
                    if word in dct['names'][i]:
                        num += 1
                if num > maxmax:
                    maxmax = num
                    indices = [i]
                elif num == maxmax:
                    indices.append(i)

            if maxmax == 0:
                fl = 1
                message = 'There is no such a construction, sorry. Try again!'
    elif search_param == 'example':
        nouns = ['noun', 'np', 'np1', 'np2', 'np3', 'xp', 'xp1', 'xp2']
        nums = ['num', 'num1', 'num2', 'xp', 'xp1', 'xp2']
        prons = ['pron', 'pronp', 'xp', 'xp1', 'xp2', 'noun', 'np', 'np1', 'np2', 'np3']
        vs = ['v', 'vp', 'vp-vp', 'vp1', 'vp2', 'cl', 'cl1', 'cl2', 'cl3']
        adjs = ['adj', 'xp', 'xp1', 'xp2']
        
        words = construction.strip('.?!').lower()
        for symbol in '(),–':
            words = words.replace(symbol, '')
        words = ' '.join(words.split('/'))
        words = (' '.join(words.split('|'))).split()
        with open('input.txt', 'w', encoding='utf-8') as f:
            f.write(' '.join(words))
        os.system("./mystem -id input.txt output.json --eng-gr --format json")
        with open('output.json', 'r', encoding='utf-8') as f:
            words = json.load(f)
        
        maxmax = 0
        indices = [0]
        for i, elem in enumerate(dct['names']):
            new = dict()
            for key, value in elem.items():
                x = value.split('\n')
                d = dict()
                for j in x:
                    d[j.split(': ')[0]] = j.split(': ')[1]
                new[key] = d
            num = 0
            for word in words:
                analyses = word['analysis']
                text = word['text']
                if text in new:
                    num += 3
                else:
                    tmp = 0
                    fl_ = 0
                    for analysis in analyses:
                        lex = analysis['lex']
                        if lex in dct['cee'][i].split() or lex in new or lex in dct['coll'][i]:
                            tmp += 2
                            break
                        gr = ','.join(analysis['gr'].split('=')).split(',')
                        if gr[0] == 'S':
                            for noun in nouns:
                                if noun in new:
                                    if 'msd' in new[noun]:
                                        lst = new[noun]['msd'].split('|')
                                        chars = dict()
                                        for y in lst:
                                            chars[y.split('=')[0]] = y.split('=')[1]
                                        br = 0
                                        for key in chars.keys():
                                            if chars[key].lower() not in gr:
                                                br = 1
                                                break
                                        if br == 1:
                                            continue
                                    tmp += 1
                                    new.pop(noun)
                                    fl_ = 1
                                    break
                        elif gr[0] == 'A':
                            for adj in adjs:
                                if adj in new:
                                    if 'msd' in new[adj]:
                                        lst = new[adj]['msd'].split('|')
                                        chars = dict()
                                        for y in lst:
                                            chars[y.split('=')[0]] = y.split('=')[1]
                                        br = 0
                                        for key in chars.keys():
                                            if chars[key].lower() not in gr:
                                                br = 1
                                                break
                                        if br == 1:
                                            continue
                                    tmp += 1
                                    new.pop(adj)
                                    fl_ = 1
                                    break
                        elif gr[0] == 'ADV':
                            if 'adv' in new:
                                if 'msd' in new['adv']:
                                    lst = new['adv']['msd'].split('|')
                                    chars = dict()
                                    for y in lst:
                                        chars[y.split('=')[0]] = y.split('=')[1]
                                    br = 0
                                    for key in chars.keys():
                                        if chars[key].lower() not in gr:
                                            br = 1
                                            break
                                    if br == 1:
                                        continue
                                tmp += 1
                                new.pop('adv')
                                fl_ = 1
                                break
                        elif gr[0] == 'CONJ':
                            if 'conj' in new:
                                tmp += 1
                                new.pop('conj')
                                fl_ = 1
                                break
                            if 'sconj' in new:
                                tmp += 1
                                new.pop('sconj')
                                fl_ = 1
                                break
                        elif gr[0] == 'INTJ':
                            if 'intj' in new:
                                tmp += 1
                                new.pop('intj')
                                fl_ = 1
                                break
                        elif gr[0] == 'NUM':
                            for num_ in nums:
                                if num_ in new:
                                    if 'msd' in new[num_]:
                                        lst = new[num_]['msd'].split('|')
                                        chars = dict()
                                        for y in lst:
                                            chars[y.split('=')[0]] = y.split('=')[1]
                                        br = 0
                                        for key in chars.keys():
                                            if chars[key].lower() not in gr:
                                                br = 1
                                                break
                                        if br == 1:
                                            continue
                                    tmp += 1
                                    new.pop(num_)
                                    fl_ = 1
                                    break
                        elif gr[0] == 'SPRO':
                            for pron in prons:
                                if pron in new:
                                    if 'msd' in new[pron]:
                                        lst = new[pron]['msd'].split('|')
                                        chars = dict()
                                        for y in lst:
                                            chars[y.split('=')[0]] = y.split('=')[1]
                                        br = 0
                                        for key in chars.keys():
                                            if chars[key].lower() not in gr:
                                                br = 1
                                                break
                                        if br == 1:
                                            continue
                                    tmp += 1
                                    new.pop(pron)
                                    fl_ = 1
                                    break
                        elif gr[0] == 'ADVPRO':
                            if 'sconj' in new:
                                tmp += 1
                                new.pop('sconj')
                                fl_ = 1
                                break
                        elif gr[0] == 'V':
                            for v in vs:
                                if v in new:
                                    if 'msd' in new[v]:
                                        lst = new[v]['msd'].split('|')
                                        chars = dict()
                                        for y in lst:
                                            chars[y.split('=')[0]] = y.split('=')[1]
                                        br = 0
                                        for key in chars.keys():
                                            if chars[key].lower() not in gr and key != 'Verb':
                                                br = 1
                                                break
                                        if br == 1:
                                            continue
                                    tmp += 1
                                    new.pop(v)
                                    fl_ = 1
                                    break
                        
                        if fl_ == 1:
                            break
                    num += tmp
                    
            if num > maxmax:
                maxmax = num
                indices = [i]
            elif num == maxmax and len(dct['names'][i].keys()) >= len(words)-2:
                if len(dct['names'][indices[-1]].keys()) > len(dct['names'][i].keys()):
                    indices = [i]
                elif len(dct['names'][indices[-1]].keys()) == len(dct['names'][i].keys()):
                    indices.append(i)

        if maxmax == 0:
            fl = 1
            message = 'There is no such a construction, sorry. Try again!'
    
    count = len(indices)
    indices = indices[PER_PAGE * (int(page) - 1): PER_PAGE * int(page)]
    pagination = Pagination(page, PER_PAGE, ceil(count / PER_PAGE))
    return render_template('output.html', lst=indices, dct=dct, fl=fl, message=message, pagination=pagination)    

@app.route('/output2/', defaults={'page': 1})
@app.route('/output2/page/<page>')
def output2(page):
    with open('data.json', 'r', encoding='utf-8') as f:
        dct = json.load(f)
    d = request.args.to_dict()
    for key in d.keys():
        d[key] = request.args.getlist(key)
    if 'strict' in d:
        d['strict'] = int(d['strict'][0])
    else:
        d['strict'] = 0
    emails = sorted(list(np.unique(np.array(dct['lastmodifiedBy']))))
    cefr = 'a1 a2 b1 b2 c1 c2'.split()
    if 'lMB' not in d:
        d['lMB'] = [i for i in range(len(emails))]
    else:
        d['lMB'] = [int(elem) for elem in d['lMB']]
    if 'cefr' not in d:
        d['cefr'] = [i for i in range(6)]
    else:
        d['cefr'] = [int(elem) for elem in d['cefr']]
    for key in ['comment', 'rus_definition', 'eng_definition', 'nor_definition', 'reference']:
        if key not in d:
            d[key] = 0
        else:
            d[key] = 1
    if 'lemmas' not in d:
        d['lemmas'] = {}
    else:
        d['lemmas'] = set(elem.strip() for elem in d['lemmas'][0].split(',') if elem != '')
    if 'pos' not in d:
        d['pos'] = set()
    else:
        d['pos'] = set(d['pos'])
    if 'role' not in d:
        d['role'] = set()
    else:
        d['role'] = set(d['role'])
    if 'msd' not in d:
        d['msd'] = set()
    else:
        d['msd'] = set(d['msd'])
    if 'aux' not in d:
        d['aux'] = set()
    else:
        d['aux'] = set(d['aux'])
    set_lemmas = deepcopy(d['lemmas'])
    set_pos = deepcopy(d['pos'])
    set_role = deepcopy(d['role'])
    set_msd = deepcopy(d['msd'])
    set_aux = deepcopy(d['aux'])
    indices = []
    min = sys.maxsize
    for i in range(len(dct['id'])):
        d['lemmas'] = deepcopy(set_lemmas)
        d['pos'] = deepcopy(set_pos)
        d['role'] = deepcopy(set_role)
        d['msd'] = deepcopy(set_msd)
        d['aux'] = deepcopy(set_aux)
        if emails.index(dct['lastmodifiedBy'][i]) not in d['lMB']:
            continue
        if not (d['date'][0] <= dct['lastmodified'][i][0] <= d['date'][1]) or not (d['appt-time'][0] <= dct['lastmodified'][i][1] <= d['appt-time'][1]):
            continue
        if dct['cefr'][i] not in cefr or cefr.index(dct['cefr'][i]) not in d['cefr']:
            continue
        fl = 0
        for key in ['comment', 'rus_definition', 'eng_definition', 'nor_definition', 'reference']:
            if d[key] == 1 and not dct[key][i]:
                fl = 1
                break
        if fl == 1:
            continue
        for key, value in dct['names'][i].items():
            tmp = {elem.split(': ')[0]:elem.split(': ')[1] for elem in value.split('\n')}
            if 'lu' in tmp.keys() and tmp['lu'] in d['lemmas']:
                d['lemmas'] -= {tmp['lu']}
            if 'cat' in tmp.keys() and tmp['cat'] in d['pos']:
                d['pos'] -= {tmp['cat']}
            if 'role' in tmp.keys() and tmp['role'] in d['role']:
                d['role'] -= {tmp['role']}
            if 'aux' in tmp.keys() and tmp['aux'] in d['aux']:
                d['aux'] -= {tmp['aux']}
            if 'msd' in tmp.keys():
                spl = tmp['msd'].split('|')
                for elem in spl:
                    if elem in d['msd']:
                        d['msd'] -= {elem}
        for key in 'lemmas pos role msd aux'.split():
            if len(d[key]) == len(locals()['set_' + key]) and len(locals()['set_' + key]):
                fl = 1
                break
        if fl == 1:
            continue
        if d['strict']:
            sum = len(d['lemmas']) + len(d['pos']) + len(d['role']) + len(d['msd']) + len(d['aux'])
            if sum < min:
                min = sum
                indices = [i]
            elif sum == min:
                indices.append(i)
        else:
            indices.append(i)
    fl = 0
    message = ''
    if not indices:
        fl = 1
        message = 'There is no such a construction, sorry. Try again!'
    if 'perpage' not in d:
        per_page = 5
    else:
        per_page = int(d['perpage'][0])
    count = len(indices)
    indices = indices[per_page * (int(page) - 1): per_page * int(page)]
    if not indices and page != 1:
        fl = 1
        message = 'There is no such a page, sorry. Try again!'
    pagination = Pagination(page, per_page, ceil(count / per_page))
    return render_template('output.html', lst=indices, dct=dct, fl=fl, message=message, pagination=pagination)

def url_for_other_page(page):
    im_dict = request.args
    args = request.args.to_dict()
    for key in 'date appt-time lMB cefr pos role aux msd'.split():
        value = im_dict.getlist(key)
        args[key] = value
    args['page'] = page
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page

def refresh_file():
    req = urllib.request.Request(HREF)
    response = urllib.request.urlopen(req)
    text = response.read().decode('utf-8')
    text = text.replace('Acton', 'Action')
    text = text.replace('N-Dat', 'NP-Dat')
    text = text.replace('NP-Nom_VP_под_шумок', 'NP-Nom_VP_под_шумóк')
    text = text.replace('числу бизнесменов', 'числу бизнесменов,')
    text = re.sub('Оценочная конструкция используется(.*?)выражения', 'Оценочная конструкция используется для выражения', text, re.DOTALL)
    if re.findall(r'<karp:text n=\"0\"\>This construction\] is used when a.*?\[participant\]Participant purchases goods, the.*?\[price\]Quantity of which equals the \[given.*?amount\]Quantity\.<\/karp\:text>', text, re.DOTALL):
        text = text.replace(re.findall(r'<karp:text n=\"0\"\>This construction\] is used when a.*?\[participant\]Participant purchases goods, the.*?\[price\]Quantity of which equals the \[given.*?amount\]Quantity\.<\/karp\:text>', text, re.DOTALL)[0], 
        '<karp:text n="0">This constrution is used when a</karp:text><karp:e n="1" name="Participant">participant</karp:e><karp:text n="2">purchases goods, the</karp:text><karp:e n="3" name="Quantity">price</karp:e><karp:text n="4">of which equals the</karp:text><karp:e n="5" name="Quantity">given amount</karp:e><karp:text n="6">.</karp:text>')
    if re.findall('<karp:text n=\"0\">Конструкция] используется для выражения\n          разочарования: \[субъект]Theme под каким-либо особенным\n          названием не способен выполнить действие, которое входит\n          в его функционал, согласно общепринятым\n          ожиданиям\.</karp:text>', text, re.DOTALL):
        text = text.replace(re.findall('<karp:text n=\"0\">Конструкция] используется для выражения\n          разочарования: \[субъект]Theme под каким-либо особенным\n          названием не способен выполнить действие, которое входит\n          в его функционал, согласно общепринятым\n          ожиданиям\.</karp:text>', text, re.DOTALL)[0],
        '<karp:text n="0">Конструкция используется для выражения разочарования:</karp:text><karp:e n="1" name="Theme">субъект</karp:e><karp:text n="2">под каким-либо особенным названием не способен выполнить действие, которое входит в его функционал, согласно общепринятым ожиданиям</karp:text><karp:text n="6">.</karp:text>')
    text = text.replace('numod', 'nummod')
    text = text.replace('NP-Nom_занимать_Num-Acc_NP-Acc', 'NP-Nom_занимать_Num-Acc_NP-Gen')
    text = text.replace('[root [nsubj NP-Nom] занимать/уходить [obl [nummod Num-Acc] NP-Acc]]', '[root [nsubj NP-Nom] занимать/уходить [obl [nummod Num-Acc] NP-Gen]]')
    text = text.replace('[root nsubj он] готов [dep сделать] [obj [amod домашнее] задание]]', '[root [nsubj он] готов [dep сделать] [obj [amod домашнее] задание]]')
    text = text.replace('iobj', 'obj')
    text = text.replace('<konst:int_const_elem cat=\"Adv\" msd=\"Adv\" name=\"Condition\"', '<konst:int_const_elem cat="Adv" msd="Adv" name="Adv"')
    text = text.replace('<konst:int_const_elem cat=\"Adv\" msd=\"Condition\" name=\"Adv\"', '<konst:int_const_elem cat="Adv" msd="Adv" name="Adv"')
    text = text.replace('[root [discourse [advmod [advmod как] всегда] XP]\"', '[root [discourse [advmod [advmod как] всегда] XP]]"')
    text = text.replace('[root XP [discourse [advmod [advmod как] всегда]]\"', '[root XP [discourse [advmod [advmod как] всегда]]]"')
    text = text.replace('[root [nsubj вы] прекрасны [discourse [advmod [advmod как] всегда]]\"', '[root [nsubj вы] прекрасны [discourse [advmod [advmod как] всегда]]]"')
    text = text.replace('как_всегда', 'как+всегда')
    text = text.replace('как,обычно', 'как, обычно')
    text = text.replace('[root [parataxis ой] [advmod как] страшно]!', '[root [parataxis ой] [advmod как] страшно!]')
    text = text.replace('[root [parataxis ой/ох/ах/ай] [advmod как] Adv]!', '[root [parataxis ой/ох/ах/ай] [advmod как] Adv!]')
    text = text.replace('<konst:int_const_elem cat=\"Pron\" name=\"Pron\"\n        role=\"Participant\" />\n        <konst:int_const_elem cat=\"Num\" name=\"Num\" role=\"Number\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />', '<konst:int_const_elem cat="Pron" name="Pron" role="Participant" /> <konst:int_const_elem cat="VP" name="VP" role="Action" /> <konst:int_const_elem cat="Adv" name="Adv" role="Adverb" />')
    text = text.replace('<karp:e n="2" name="Number">троих</karp:e>', '<karp:e n="2" name="Adverb">троих</karp:e>')
    text = text.replace('<karp:e n="2" name="Theme">вдвоем</karp:e>', '<karp:e n="2" name="Adverb">вдвоем</karp:e>')
    text = text.replace('<karp:e n="2" name="Number">втроем</karp:e>', '<karp:e n="2" name="Adverb">втроем</karp:e>')
    text = text.replace('Цитировать</karp:e>', 'цитировать</karp:e>')
    text = text.replace('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"VP-Dat\" role=\"Source\" />', '<konst:int_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat" role="Source" />')
    text = text.replace('всего-навсего_NP-Nom', 'всего-навсего+NP-Nom')
    text = text.replace('Noun-Nom', 'NP-Nom')
    text = text.replace('[root [nsubj NP-Nom] называется]\"', '[root [nsubj NP-Nom] называется!]"')
    text = text.replace('<karp:e n="1" name="Theme">The subject</karp:e>', '<karp:e n="1" name="Theme">the subject</karp:e>')
    text = text.replace('[root переименовать [obl NP-Acc [[case в] NP-Acc]]]', '[root переименовать [obl NP-Acc [case в] NP-Acc]]')
    text = text.replace('[root переименовать [obl Ленинград [[case в] Санкт-Петербург]]]', '[root переименовать [obl Ленинград [case в] Санкт-Петербург]]')
    text = text.replace('<konst:int_const_elem cat=\"Pron\" msd=\"PronType=Interrog\"\n        name=\"Pron\" role=\"Theme\" />', '<konst:int_const_elem cat="SCONJ" msd="PronType=Interrog" name="SCONJ" role="Theme" />')
    text = text.replace('[root [amod каков] NP-Nom]', '[root [amod каков] NP-Nom!]')
    names = re.findall('name=\".*?\"', text)
    for name in names:
        if '_' in name:
            tmp = name.split('"')
            text = text.replace(name, tmp[0] + '"' + tmp[1].replace('_', '+') + '"')
    text = text.replace('konstruktikon-rus--c_NP-Ins_(NP-Acc)', 'konstruktikon-rus--с_NP-Ins_(NP-Acc)')
    text = text.replace('<karp:e n="0" name="Theme">Женщины</karp:e>', '<karp:e n="0" name="Theme">женщины</karp:e>')
    text = re.sub('<konst:int_const_elem cat=\"VP\" msd=\"VerbType=Past/Pres\"\n        name=\"Action\" role=\"Action\" />', '<konst:int_const_elem cat="VP" msd="VerbType=Past/Pres" name="VP" role="Action" />', text)
    text = text.replace('но, счастью, его вовремя отвлёк', 'но, к счастью, его вовремя отвлёк')
    text = text.replace('телефонный звонокю', 'телефонный звонок')
    text = text.replace('name="Noun" role="Theme" />', 'name="NP-Nom" role="Theme" />')
    text = re.sub('<karp:text n=\"5\">\!</karp:text>\n          <\/karp:e>\n          <karp:g n=\"2\" />\n          <karp:text n=\"3\">\!', '\n        </karp:e>\n        <karp:g n="2" />\n        <karp:text n="3">!', text)
    text = text.replace('[root [nsubj (NP-Nom)] [advmod только[fixed что]] VP-Perf.Past]', '[root [nsubj (NP-Nom)] [advmod только [fixed что]] VP-Perf.Past]')
    text = re.sub('<karp:e n=\"1\" name=\"Participant\">Министр\n            образовани</karp:e>\n            <karp:g n=\"2\" />\n            <karp:text n=\"3\">я</karp:text>', '<karp:e n="1" name="Participant">Министр образования</karp:e>', text)
    text = text.replace('[root [advmod не] дом [nmod [case у] них], [conj [cc а ] [amod столярная] мастерская.]]', '[root [advmod не] дом [nmod [case у] них], [conj [cc а] [amod столярная] мастерская.]]')
    text = text.replace('[хоть NP], [хоть NP]', 'root [хоть NP], [хоть NP]')
    text = text.replace('<konst:int_const_elem cat="Verb" lu="стоить" name="cтоить"', '<konst:int_const_elem cat="Verb" lu="стоить" name="стоить"')
    text = text.replace('name="Action" role="Action" />', 'name="VP" role="Action" />')
    text = text.replace('[root [advmod только] [aux бы] [advmod не] VP]', '[root [advmod только] [aux бы] [advmod не] VP!]')
    text = text.replace('<karp:e n="4" name="Participant">папы</karp:e>', '<karp:e n="4" name="Participant">папы,</karp:e>')
    text = text.replace('msd="AdjectiveType=Comparative" name="AP-Cmp"', 'msd="AdjectiveType=Comparative" name="Adv-Cmp"') # Что-то непонятное
    text = text.replace('konstruktikon-rus--NP-Nom_Adv-Cmp,_чем_NP-Nom', 'konstruktikon-rus--NP-Nom1_Adv-Cmp,_чем_NP-Nom2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Prototype\" />', '<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom1\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom2\" role=\"Prototype\" />', text)
    text = text.replace('konstruktikon-rus--Noun-то!', 'konstruktikon-rus--NP-Nom_-то!')
    text = text.replace('[root [advmod едва] [fixed ли]] [nsubj Паша] заплатит]', '[root [advmod едва [fixed ли]] [nsubj Паша] заплатит]')
    text = text.replace('генитива: Желаю вам счастливого пути.</karp:text>', 'генитива: "Желаю вам счастливого пути".</karp:text>')
    text = text.replace('konstruktikon-rus--NP-Dat_стоить_VP-Inf', 'konstruktikon-rus--NP-Dat_стоит_VP-Inf')
    text = text.replace('konstruktikon-rus--по-XP-ее(ей)', 'konstruktikon-rus--по-_XP_-ее(ей)')
    text = text.replace('"konstruktikon-rus--NP-Gen.Plur_Num"', '"konstruktikon-rus--NP-Gen.Plur_Num-Nom"')
    text = text.replace('name="NUM-Nom" role="Number" />', 'name="Num-Nom" role="Number" />')
    text = text.replace('<karp:e n="2" name="Number">20― 30</karp:e>', '<karp:e n="2" name="Number">20-30</karp:e>')
    text = re.sub('<karp:text n=\"0\">\[\[Некоторые семьи\]Participant\| \[ни\]ни\n          \[в\]в \[какую\]какую \[не\]не \[желают рассматривать]]Action\|\n          ]NP-Nom_ни_в_какую_не_VP в качестве возможной супруги\n          девушку другой национальности\.</karp:text>', '<karp:e n="0" name="NP-Nom+ни+в+какую+не+VP"><karp:e n="0" name="Participant">Некоторые семьи</karp:e><karp:text n="1" /><karp:e n="2" name="в">ни</karp:e><karp:text n="3" /><karp:e n="4" name="в">в</karp:e><karp:text n="5" /><karp:e n="6" name="какую">какую</karp:e><karp:text n="7" /><karp:e n="8" name="не">не</karp:e><karp:text n="9" /><karp:e n="10" name="Action">желают рассматривать</karp:e><karp:g n="11" /><karp:text n="12" /></karp:e><karp:text n="1">в качестве возможной супруги девушку другой национальности.</karp:text>', text)
    text = text.replace('konstruktikon-rus--другой_NP-Nom.Sing', 'konstruktikon-rus--другой_NP-Nom')
    text = text.replace('<karp:e n="1" name="Theme">некоторого объекта</karp:e>', '<karp:e n="1" name="Theme.">некоторого объекта</karp:e>')
    text = text.replace('<karp:e n="1" name="Theme">of an object</karp:e>', '<karp:e n="1" name="Theme.">of an object</karp:e>')
    text = text.replace('[root [mark а] [mark что [fixed насчёт]] пятницы?] Какие у тебя планы?', '[root [mark а] [mark что [fixed насчёт]] пятницы? Какие у тебя планы?]')
    text = text.replace('"[advmod ох] [advmod и] умны [nsubj девушки!]]"', '"[root [advmod ох] [advmod и] умны [nsubj девушки!]]"')
    text = text.replace('[advmod ох] [advmod и] AP-Short [nsubj NP-Nom]]', '[root [advmod ох] [advmod и] AP-Short [nsubj NP-Nom!]]')
    text = text.replace('[root NP] [nmod [case из] NP-Gen.Plur]]', '[root NP [nmod [case из] NP-Gen.Plur]]')
    text = text.replace('[root король] [nmod [case из] королей]]', '[root король [nmod [case из] королей]]')
    text = re.sub('<konst:int_const_elem lu=\"иметь\"\n        msd=\"VerbType=Imperfective\" name=\"иметь\" />\n        <konst:int_const_elem lu=\"вес\" name=\"вес\" />', '<konst:int_const_elem lu="иметь" msd="VerbType=Imperfective" name="иметь" /><konst:int_const_elem lu="вес" name="вес" /><konst:int_const_elem lu="при/в" name="при/в" role="при/в" />', text)
    text = text.replace('konstruktikon-rus--такой_же_XP_как_и_NP', 'konstruktikon-rus--такой_же_XP,_как_и_NP')
    text = text.replace('[root NP [amod [amod такой] [advmod же]] XP] [nmod [cc как] [advmod и] NP]]', '[root NP [amod [amod такой] [advmod же] XP] [nmod [cc как] [advmod и] NP]]')
    text = text.replace('konstruktikon-rus--NP-Nom_VP_как_NP-Nom', 'konstruktikon-rus--NP-Nom1_VP_как_NP-Nom2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Agent\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem lu=\"как\" name=\"как\" role=\"как\" />\n        <konst:int_const_elem aux=\"animate\" cat=\"NP\"\n        msd=\"NounType=Nom\" name=\"NP-Nom\" role=\"Theme\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Agent" /><konst:int_const_elem cat="VP" name="VP" role="Action" /><konst:int_const_elem lu="как" name="как" role="как" /><konst:int_const_elem aux="animate" cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Theme" />', text)
    text = text.replace('<konst:int_const_elem name="пусть" />', '<konst:int_const_elem name="пусть" cat="Particle" />')
    text = text.replace('konstruktikon-rus--NP-Nom_NP-Nom_VP-Inf', 'konstruktikon-rus--NP-Nom1_NP-Nom2_VP-Inf')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Protagonist\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Evaluation\" />\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Inf\"\n        name=\"VP-Inf\" role=\"Action\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Protagonist" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Evaluation" /><konst:int_const_elem cat="VP" msd="VerbType=Inf" name="VP-Inf" role="Action" />', text)
    text = text.replace('<karp:text n="3">, Леночка</karp:text>', '<karp:text n="3">, Леночка,</karp:text>')
    text = text.replace('msd="VerbType=PST" name="пристало" role="пристало" />', 'msd="VerbType=PST" name="пристать" role="пристало" />')
    text = text.replace('[root [parataxis ну] [advmod и] NP]', '[root [parataxis ну] [advmod и] NP!]')
    text = text.replace('konstruktikon-rus--NP-Nom_VP,_не_то_что_NP-Nom', 'konstruktikon-rus--NP-Nom1_VP,_не_то_что_NP-Nom2')
    text = re.sub('<konst:int_const_elem cat=\"Particle\" lu=\"не\"\n        msd=\"PartType=Neg\" name=\"не\" role=\"не\" />\n        <konst:int_const_elem cat=\"Particle\" lu=\"то\" name=\"то\"\n        role=\"то\" />\n        <konst:int_const_elem cat=\"Particle\" lu=\"что\" name=\"что\"\n        role=\"что\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Participant\" />\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Situation\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Standard" /><konst:int_const_elem cat="VP" msd="VerbType=Pst" role="Action" /><konst:int_const_elem cat="Particle" lu="не" msd="PartType=Neg" name="не" role="не" /><konst:int_const_elem cat="Particle" lu="то" name="то" role="то" /><konst:int_const_elem cat="Particle" lu="что" name="что" role="что" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Theme" />', text)
    text = text.replace('[root [nsubj он] [cop был] [amod настоящим] другом], [conj [advmod [advmod не] то [fixed что]] [amod твой] брат]]', '[root [nsubj он] [cop был] [amod настоящим] другом, [conj [advmod [advmod не] то [fixed что]] [amod твой] брат]]')
    text = text.replace('[root VP-Inf [obj NP-Dat] [advmod негде]]', '[root VP-Inf [obj NP-Dat] [advmod негде.]]')
    text = text.replace('<karp:e n="1" name="Action">Action</karp:e>', '<karp:e n="1" name="Action">action</karp:e>')
    text = text.replace('родителями</karp:e>', 'родителями,</karp:e>')
    text = text.replace('konstruktikon-rus--NP-Nom_сделаться_NP/Adj-Ins', 'konstruktikon-rus--NP-Nom_сделаться_NP-Ins/Adj-Ins')
    text = text.replace('<karp:e n="2" name="в">это</karp:e>', '<karp:e n="2" name="это">это</karp:e>')
    text = re.sub('<konst:int_const_elem cat=\"VP\" lu=\"мочь\" name=\"мочь\"\n        role=\"мочь\" />', '<konst:int_const_elem cat="VP-Past" lu="мочь" name="мочь-Past" role="мочь" />', text)
    text = text.replace('[root [amod своего] рода] NP]', '[root [amod своего] рода NP]')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"PronType=Nom\"\n        name=\"Object\" role=\"Stimulus\" />', '<konst:int_const_elem cat="NP" msd="PronType=Nom" name="NP-Nom" role="Stimulus" />', text)
    text = text.replace('[root [advmod ай] [advmod да] NP-Nom]', '[root [advmod ай] [advmod да] NP-Nom!]')
    text = text.replace('<karp:e n=\"0\" name=\"ай\">Ай</karp:e>\n            <karp:text n=\"1\" />\n            <karp:e n=\"2\" name=\"да\">да</karp:e>\n            <karp:text n=\"3\" />\n            <karp:e n=\"4\" name=\"Evaluation\">Хрипушин</karp:e>', '<karp:e n="0" name="ай">«Ай</karp:e><karp:text n="1" /><karp:e n="2" name="да">да</karp:e><karp:text n="3" /><karp:e n="4" name="Evaluation">Хрипушин</karp:e>')
    text = text.replace('konstruktikon-rus--NP-Nom_как_NP-Nom', 'konstruktikon-rus--NP-Nom1_как_NP-Nom2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Standard\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Theme" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Standard" />', text)
    text = text.replace('<karp:e n="5" name="Standard">город</karp:e>', '<karp:e n="5" name="Standard.">город</karp:e>')
    text = text.replace('[root [advmod что [advmod же]] [nsubj NP-Nom] VP]', '[root [advmod что [advmod же]] [nsubj NP-Nom] VP?]')
    text = text.replace('[root [nsubj Они] действовали] [obl [case на] основе] [nmod инструкции]]', '[root [nsubj они] действовали [obl [case на] основе] [nmod инструкции]]')
    text = text.replace('konstruktikon-rus--Cl_будь_то_NP_или_NP', 'konstruktikon-rus--Cl_будь_то_NP1_или_NP2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Actant\" />', '<konst:int_const_elem cat="NP" name="NP1" role="Theme" /><konst:int_const_elem cat="NP" name="NP2" role="Actant" />', text)
    text = text.replace('[root [cop будь] [nsubj то] врач [conj [cc или] учитель]] [parataxis [nsubj они [aux бы] спасли [obj человека]]]', '[root [cop будь] [nsubj то] врач [conj [cc или] учитель] [parataxis [nsubj они [aux бы] спасли [obj человека]]]')
    text = re.sub('<karp:e n=\"0\" name=\"Topic\">Есть вечные\n            ценности</karp:e>\n            <karp:g n=\"1\" />\n            <karp:text n=\"2\">,</karp:text>\n            <karp:e n=\"3\" name=\"Theme\">\n              <karp:e n=\"0\" name=\"будь\">будь</karp:e>\n              <karp:text n=\"1\" />\n              <karp:e n=\"2\" name=\"то\">то</karp:e>\n              <karp:text n=\"3\">музыка</karp:text>\n              <karp:e n=\"4\" name=\"или\">или</karp:e>\n              <karp:text n=\"5\">живопись</karp:text>\n            </karp:e>\n            <karp:g n=\"4\" />\n            <karp:text n=\"5\" />', '<karp:e n="0" name="Topic">Есть вечные ценности</karp:e><karp:g n="1" /><karp:text n="2">,</karp:text><karp:g n="3" /><karp:e n="0" name="будь">будь</karp:e><karp:text n="1" /><karp:e n="2" name="то">то</karp:e><karp:e n="3" name="Theme">музыка</karp:e><karp:e n="4" name="или">или</karp:e><karp:e n="5" name="Actant">живопись</karp:e><karp:text n="5" />', text)
    text = re.sub('<karp:e n=\"0\" name=\"Topic\">Он начинал скучать по своему\n            городу в любом другом месте</karp:e>\n            <karp:g n=\"1\" />\n            <karp:text n=\"2\">,</karp:text>\n            <karp:e n=\"3\" name=\"Theme\">\n              <karp:e n=\"0\" name=\"будь\">будь</karp:e>\n              <karp:text n=\"1\" />\n              <karp:e n=\"2\" name=\"то\">то</karp:e>\n              <karp:text n=\"3\">внутри страны</karp:text>\n              <karp:e n=\"4\" name=\"или\">или</karp:e>\n              <karp:text n=\"5\">за границей</karp:text>\n            </karp:e>\n            <karp:g n=\"4\" />\n            <karp:text n=\"5\" />', '<karp:e n="0" name="Topic">Он начинал скучать по своему городу в любом другом месте</karp:e><karp:g n="1" /><karp:text n="2">,</karp:text><karp:g n="3" /><karp:e n="0" name="будь">будь</karp:e><karp:text n="1" /><karp:e n="2" name="то">то</karp:e><karp:e n="3" name="Theme">внутри страны</karp:e><karp:e n="4" name="или">или</karp:e><karp:e n="5" name="Actant.">за границей</karp:e><karp:g n="4" /><karp:text n="5" />', text)
    text = re.sub('<karp:text n=\"0\">Потому что в любом деле,</karp:text>\n          <karp:e n=\"1\" name=\"будь\+то\+NP\+или\+NP\">\n            <karp:e n=\"0\" name=\"Theme\">\n              <karp:e n=\"0\" name=\"будь\">будь</karp:e>\n              <karp:text n=\"1\" />\n              <karp:e n=\"2\" name=\"то\">то</karp:e>\n              <karp:text n=\"3\">бизнес</karp:text>\n              <karp:e n=\"4\" name=\"или\">или</karp:e>\n              <karp:text n=\"5\">другая деятельность</karp:text>\n            </karp:e>\n            <karp:g n=\"1\" />\n            <karp:g n=\"2\" />\n            <karp:text n=\"3\">,</karp:text>\n            <karp:e n=\"4\" name=\"Topic\">главное ― это люди\.</karp:e>\n          </karp:e>', '<karp:text n="0">Потому что в любом деле,</karp:text><karp:e n="0" name="будь">будь</karp:e><karp:text n="1" /><karp:e n="2" name="то">то</karp:e><karp:e n="3" name="Theme">бизнес</karp:e><karp:e n="4" name="или">или</karp:e><karp:e n="5" name="Actant">другая деятельность</karp:e><karp:g n="2" /><karp:text n="3">,</karp:text><karp:e n="4" name="Topic">главное ― это люди.</karp:e>', text)
    text = text.replace('[nsubj что] касается [obl NP-Gen], [conj [cc то] Cl]', '[nsubj что касается [obl NP-Gen], [conj [cc то] Cl]]')
    text = text.replace('[nsubj Что] касается [obl спорта], [conj [cc то] [nsubj я] [advmod никогда] [advmod не] любил [xcomp бегать]]]', '[nsubj что касается [obl спорта], [conj [cc то] [nsubj я] [advmod никогда] [advmod не] любил [xcomp бегать]]]')
    text = re.sub('<karp:e n=\"0\" name=\"со\+временем\+Cl\">\n            <karp:e n=\"0\" name=\"Event\">\n              <karp:text n=\"0\">В парижском спектакле какие-то\n              изменения</karp:text>\n              <karp:e n=\"1\" name=\"со\">со</karp:e>\n              <karp:text n=\"2\" />\n              <karp:e n=\"3\" name=\"временем\">временем</karp:e>\n              <karp:text n=\"4\">всё-таки происходят\.</karp:text>\n            </karp:e>\n            <karp:text n=\"1\" />\n          </karp:e>', '<karp:e n="0" name="со+временем+Cl"><karp:e n="0" name="Event">В парижском спектакле какие-то изменения</karp:e><karp:e n="1" name="со">со</karp:e><karp:text n="2" /><karp:e n="3" name="временем">временем</karp:e><karp:text n="4">всё-таки происходят.</karp:text></karp:e><karp:text n="1" />', text)
    text = text.replace('msd="VerbType=2SG, FUT" name="проведёшь"', 'msd="VerbType=2SG, FUT" name="проведешь"')
    text = text.replace('konstruktikon-rus--в_глубине_души_NP-Nom_VP,(_что_Cl)', 'konstruktikon-rus--в_глубине_души_NP-Nom_VP,_(что_Cl)')
    text = text.replace('<karp:e n="5" name="Theme">noe</karp:e>', '<karp:e n="5" name="Theme">Noe</karp:e>')
    text = text.replace('[X]Theme', '[X]_Theme')
    text = text.replace('lies [about Y] to my friends’.</karp:text>', 'lies about Y to my friends’.</karp:text>')
    text = text.replace('<karp:text n="2">. Этот объект не представляет', '<karp:text n="2">Этот объект не представляет')
    text = text.replace('[root [obl [case в] условиях [nmod подъёма [nmod экономики]] [nmod России]]]], выросла [nmod роль [nmod [amod временных] миграций]]]', '[root [obl [case в] условиях [nmod подъёма [nmod экономики]] [nmod России]], выросла [nmod роль [nmod [amod временных] миграций]]]')
    text = text.replace('[advmod [fixed как] можно] Adv-Cmp/Adj-Cmp]] VP]', '[advmod [fixed как] можно Adv-Cmp/Adj-Cmp VP]')
    text = re.sub('<konst:int_const_elem cat=\"Adj\" msd=\"AdjType=Cmp\"\n        name=\"Adj\" role=\"Property\" />', '<konst:int_const_elem cat="Adj" msd="AdjType=Cmp" name="Adj-ее" role="Property" />', text)
    text = re.sub('<konst:int_const_elem lu=\"сломить\" name=\"сломить\"\n        role=\"сломить\" />\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Agent\" />', '<konst:int_const_elem lu="сломить" name="сломить" role="сломить" /><konst:int_const_elem cat="NP" name="NP-Dat" role="Agent" />', text)
    text = re.sub('<konst:int_const_elem lu=\"жизнь\" name=\"жизни\"\n        role=\"жизни\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Action\" />', '<konst:int_const_elem lu="жизнь" name="жизни" role="жизни" /><konst:int_const_elem cat="Particle" lu="не" msd="PartType=Neg" name="не" role="не" /><konst:int_const_elem cat="Cl" name="Cl" role="Action" />', text)
    text = text.replace('name="характер" role="характер" />', 'name="характер-Acc" role="характер" />')
    text = text.replace('[root носить [obj [amod Adj-Acc] характер-Acc]', '[root носить [obj [amod Adj-Acc] характер-Acc.]')
    text = text.replace('konstruktikon-rus--NP-Nom-Noun-Ins_а/но_Cl', 'konstruktikon-rus--NP-Nom_Noun-Ins_а/но_Cl')
    text = text.replace('[root [nsubj NP-Nom]-Noun-Ins [conj [cc а/но] Cl]]', '[root [nsubj NP-Nom] Noun-Ins [conj [cc а/но] Cl]]')
    text = text.replace('konstruktikon-rus--NP-Nom_NP-Dat_не_NP-Nom', 'konstruktikon-rus--NP-Nom1_NP-Dat_не_NP-Nom2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Stimulus\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Evaluation\" />\n        <konst:int_const_elem cat=\"Participle\" lu=\"не\"\n        msd=\"PartType=Neg\" name=\"не\" role=\"не\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"NP-Dat\" role=\"Experiencer\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Stimulus" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Evaluation" /><konst:int_const_elem cat="Participle" lu="не" msd="PartType=Neg" name="не" role="не" /><konst:int_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat" role="Experiencer" />', text)
    text = text.replace('konstruktikon-rus--время от времени Cl', 'konstruktikon-rus--время_от_времени_Cl')
    text = text.replace('[root [advmod время [obl [case от] времени] ] Cl]', '[root [advmod время [obl [case от] времени]] Cl]')
    text = text.replace('[root [advmod время [obl [case от] времени] ] [nsubj я] перестаю [xcomp [obj что-либо] успевать]', '[root [advmod время [obl [case от] времени]] [nsubj я] перестаю [xcomp [obj что-либо] успевать]')
    text = re.sub('<definition xml:lang=\"nor\">\n          <karp:text n=\"0\">Konstruksjonen betyr at</karp:text>\n          <karp:e n=\"1\" name=\"Event\">noe</karp:e>\n          <karp:text n=\"2\">skjer av og til\. En nærliggende\n          konstruksjon i norsk er ‘fra tid til annen’\.</karp:text>\n        </definition>\n      </Sense>\n    </LexicalEntry>', '<definition xml:lang="nor"><karp:text n="0">Konstruksjonen betyr at</karp:text><karp:e n="1" name="Event">noe</karp:e><karp:text n="2">skjer av og til. En nærliggende konstruksjon i norsk er ‘fra tid til annen’.</karp:text></definition><konst:int_const_elem cat="NP" lu="время" msd="NounType=Nom" name="время" role="время" /><konst:int_const_elem lu="от" name="от" role="от" /><konst:int_const_elem cat="NP" lu="время" msd="NounType=Gen" name="времени" role="время" /><konst:int_const_elem cat="Clause" name="Cl" role="Situation" /></Sense></LexicalEntry>', text)
    text = text.replace('<karp:text n="2">затем наоборот―', '<karp:text n="2">затем наоборот ―')
    text = re.sub('<karp:text n="0">Время от времени</karp:text>', '<karp:e n="0" name="время">Время</karp:e><karp:e n="0" name="от">от</karp:e><karp:e n="0" name="времени">времени</karp:e>', text)
    text = re.sub('<karp:text n="0">Не забудьте время от времени</karp:text>', '<karp:text n="0">Не забудьте</karp:text><karp:e n="0" name="время">время</karp:e><karp:e n="0" name="от">от</karp:e><karp:e n="0" name="времени">времени</karp:e>', text)
    text = text.replace('<karp:text n="2">но у каждого из них цель― не создание', '<karp:text n="2">но у каждого из них цель ― не создание')
    text = text.replace('<karp:e n="1" name=",">noe annet</karp:e>', '<karp:e n="1" name="Theme,">noe annet</karp:e>')
    text = text.replace('konstruktikon-rus--NP-Nom_всё_V-Imp', 'konstruktikon-rus--NP-Nom_всё_VP-Imp')
    text = text.replace('<karp:e n="1" name="Goal">сообытие</karp:e>', '<karp:e n="1" name="Goal">событие</karp:e>')
    text = text.replace('[root [cc чтобы] NP-Gen [nmod NP]/[advmod Adv] [advmod не] [cop было]]', '[root [cc чтобы] NP-Gen [  [nmod NP] / [advmod Adv]] [advmod не] [cop было!]]')
    text = text.replace('<karp:e n="1" name="XXX">someone or something</karp:e>', '<karp:e n="1" name="Recipient">someone or something</karp:e>')
    text = text.replace('<karp:e n="1" name="XXX">noe eller noen</karp:e>', '<karp:e n="1" name="Recipient">noe eller noen</karp:e>')
    text = text.replace('konstruktikon-rus--NP-Nom_не_играть_(никакой)_роль', 'konstruktikon-rus--NP-Nom_не_играть_(никакой)_роли')
    text = text.replace('konstruktikon-rus--то_ли_XP_то_ли_XP', 'konstruktikon-rus--то_ли_XP,_то_ли_XP')
    text = text.replace('[root [xmod [cc то ли] XP], [conj[cc то ли] XP]]', '[root [xmod [cc то ли] XP], [conj [cc то ли] XP]]')
    text = text.replace('<karp:e n="1" name="Theme.">некоторого объекта</karp:e>', '<karp:e n="1" name="Theme">некоторого объекта</karp:e>')
    text = text.replace('[root [nsubj время [nmod NP-Gen]] ([advmod не]) пришло]', '[root [nsubj время [nmod NP-Gen]] [(advmod не)] пришло]')
    text = text.replace('<konst:int_const_elem lu="незьзя" name="нельзя" />', '<konst:int_const_elem lu="нельзя" name="нельзя" />')
    text = text.replace('konstruktikon-rus--чтоб(ы)_Pron-Nom_V-Past!', 'konstruktikon-rus--чтоб_(чтобы)_Pron-Nom_V-Past!')
    text = text.replace('[root [cc чтобы] [nsubj он] опоздал!]', '[root [cc чтоб(ы)] [nsubj он] опоздал!]')
    text = text.replace('<konst:int_const_elem msd="NounType=Gen" name="NP"', '<konst:int_const_elem msd="NounType=Gen" name="NP-Gen"')
    text = re.sub('<konst:int_const_elem lu=\"всё\" name=\"всё\" role=\"всё\" />\n        <konst:int_const_elem msd=\"AdjType=Cmp\" name=\"Adj-Cmp\"\n        role=\"Property\" />\n        <konst:int_const_elem cat=\"Adv\" msd=\"AdvType=Cmp\"\n        name=\"Adv-Cmp\" role=\"Property\" />', '<konst:int_const_elem lu="всё" name="всё" role="всё" /><konst:int_const_elem msd="AdjType=Cmp" name="Adj-Cmp" role="Property" /><konst:int_const_elem cat="Conjunction" lu="и" name="и" role="и" /><konst:int_const_elem cat="Adv" msd="AdvType=Cmp" name="Adv-Cmp" role="Property" />', text)
    text = text.replace('<karp:e n="1" name=",">en viss egenskap</karp:e>', '<karp:e n="1" name="Property,">en viss egenskap</karp:e>')
    text = text.replace('name=" VP-Inf" role="Action" />', 'name="VP-Inf" role="Action" />')
    text = re.sub('<konst:int_const_elem cat=\"Particle\" lu=\"далеко\"\n        name=\"далеко\" role=\"далеко\" />\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"Particle\" lu=\"не\" name=\"не\"\n        role=\"не\" />', '<konst:int_const_elem cat="Particle" lu="далеко" name="далеко" role="далеко" /><konst:int_const_elem cat="NP" name="NP" role="Theme" /><konst:int_const_elem cat="Adj" msd="AdjType=Plen" name="Adj" role="Property" /><konst:int_const_elem cat="Adv" name="Adv" role="Theme" /><konst:int_const_elem cat="Particle" lu="не" name="не" role="не" />', text)
    text = text.replace('[root [nsubj NP-Nom] [advmod далеко] [advmod не] [amod Adj/] [advmod Adv] NP]', '[root [nsubj NP-Nom] [advmod далеко] [advmod не] [  [amod Adj] or [advmod Adv]] NP]')
    text = re.sub('<konst:int_const_elem lu=\"все\" name=\"все\" role=\"все\" />\n        <konst:int_const_elem lu=\"до\" name=\"до\" role=\"до\" />\n        <konst:int_const_elem lu=\"единый\" msd=\"Type=Gen\"\n        name=\"единый-Gen\" role=\"единый\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Theme\" />', '<konst:int_const_elem lu="все" name="все" role="все" /><konst:int_const_elem lu="до" name="до" role="до" /><konst:int_const_elem lu="единый" msd="Type=Gen" name="единый-Gen" role="единый" /><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /><konst:int_const_elem cat="NP" name="NP" role="Theme" />', text)
    text = text.replace('<konst:int_const_elem name="NP-Dat" />', '<konst:int_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat" role="Experiencer" />')
    text = re.sub('<karp:text n=\"0\">Мне</karp:text>\n          <karp:e n=\"1\" name=\"VP-Inf\+некуда\">', '<karp:e n="0" name="Experiencer">Мне</karp:e><karp:e n="1" name="VP-Inf+некуда">', text)
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Agent\" />\n        <konst:int_const_elem lu=\"идти\" msd=\"VerbType=Imperfective\"\n        name=\"идти\" role=\"идти\" />\n        <konst:int_const_elem lu=\"за\" name=\"за\" role=\"за\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"NP-Dat\" role=\"Theme\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom" role="Agent" /><konst:int_const_elem lu="идти" msd="VerbType=Imperfective" name="идти" role="идти" /><konst:int_const_elem lu="за" name="за" role="за" /><konst:int_const_elem cat="NP" msd="NounType=Ins" name="NP-Ins" role="Theme" />', text)
    text = text.replace('последовательно или одновременно. Ударени в слове "связи"', 'последовательно или одновременно. Ударение в слове "связи"')
    text = text.replace('[root [obl чего] лежишь]', '[root [obl чего] лежишь?]')
    text = text.replace('[root [obl чего] VP]', '[root [obl чего] VP?]')
    text = re.sub('<konst:int_const_elem lu=\"Что\" name=\"Чего\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />', '<konst:int_const_elem lu="Что" name="Чего" /><konst:int_const_elem lu="это" name="это" role="это" /><konst:int_const_elem cat="VP" name="VP" role="Action" />', text)
    text = re.sub('<konst:int_const_elem lu=\"все\" name=\"все\" role=\"все\" />\n        <konst:int_const_elem cat=\"Num\" name=\"Num\" role=\"Number\" />\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Theme\" />\n      </Sense>', '<konst:int_const_elem lu="все" name="все" role="все" /><konst:int_const_elem cat="Num" name="Num" role="Number" /><konst:int_const_elem cat="NP" msd="NounType=Gen" name="NP-Gen" role="Theme" /><konst:int_const_elem cat="VP" name="VP" role="Action" /></Sense>', text)
    text = text.replace('konstruktikon-rus--все_NUM_NP-Gen_(VP)', 'konstruktikon-rus--все_Num_NP-Gen_(VP)')
    text = text.replace('NUM', 'Num')
    text = text.replace('[root живут [advmod же] [nsubj некоторые]]', '[root живут [advmod же] [nsubj некоторые!]]')
    text = text.replace('<konst:int_const_elem lu="отличаться" name="отличается"', '<konst:int_const_elem lu="отличаться" name="отличаться"')
    text = text.replace('konstruktikon-rus--чем_Adj-Cmp/Adv-Cmp_тем_Adj-Cmp/Adv-Cmp', 'konstruktikon-rus--чем_Adj-Cmp/Adv-Cmp,_тем_Adj-Cmp/Adv-Cmp')
    text = text.replace('чем больше тем лучше', 'чем больше, тем лучше')
    text = re.sub('<karp:e n=\"3\"\n          name=\"чем\+Adj-Cmp/Adv-Cmp\+тем\+Adj-Cmp/Adv-Cmp\">\n            <karp:e n=\"0\" name=\"чем\">Чем</karp:e>', '<karp:e n="3" name="чем+Adj-Cmp/Adv-Cmp+тем+Adj-Cmp/Adv-Cmp"><karp:e n="0" name="чем">чем</karp:e>', text)
    text = text.replace('<karp:e n="1" name="XXX,">do X</karp:e>', '<karp:e n="1" name="Action,">do X</karp:e>')
    text = text.replace('<karp:e n="1" name="XXX,">gjøre X</karp:e>', '<karp:e n="1" name="Action,">gjøre X</karp:e>')
    text = text.replace('[root [obl Pro-Dat [avmod ли]] [advmod не] VP-Inf]', '[root [obl Pro-Dat [avmod ли]] [advmod не] VP-Inf!]')
    text = text.replace('konstruktikon-rus--как_ни_VP_Cl', 'konstruktikon-rus--как_ни_VP,_Cl')
    text = text.replace('[root [nsubj я] [obj тебя] [xcomp терпеть] [xcomp не] могу!] [xcomp соревноваться]]', '[root [nsubj я] [obj тебя] [xcomp терпеть] [xcomp не] могу!] [xcomp соревноваться]]')
    text = text.replace('[root [nsubj NP-Nom] [xcomop терпеть] [advmod не] мочь [obj NP-Acc]]/ [xcomp VP-Inf.Imp]]', '[root [nsubj NP-Nom] [xcomop терпеть] [advmod не] мочь [  [obj NP-Acc] or [xcomp VP-Inf.Imp]]]')
    text = text.replace('наи-А-ший', 'наи-Аdj-ший')
    text = text.replace('наи-A-ший', 'наи-Adj-ший')
    text = text.replace('<karp:e n="6" name="Отдать+в/на+NP-Acc">Свердловский', '<karp:e n="6" name="Location">Свердловский')
    text = text.replace('konstruktikon-rus--зайти_VP-Inf.Perf', 'konstruktikon-rus--зайти_VP-Inf')
    text = text.replace('konstruktikon-rus--NP-Nom_NP-Dat_показать-VP-Fut!', 'konstruktikon-rus--NP-Nom_NP-Dat_показать!')
    text = text.replace('<konst:int_const_elem lu="показать" name="показать" />', '<konst:int_const_elem lu="показать" cat="VP" name="показать" msd="VerbType=Fut" />')
    text = text.replace('konstruktikon-rus--Noun_NP-Gen.Plur', 'konstruktikon-rus--NP-Nom_NP-Gen.Plur')
    text = text.replace('[root [parataxis INTJ] [amod какой [amod Adj-Nom] NP-Nom]!', '[root [parataxis INTJ] [amod какой [amod Adj-Nom] NP-Nom!]]')
    text = text.replace('[root [parataxis ой], [amod какой [amod горячий] хлеб]!', '[root [parataxis ой], [amod какой [amod горячий] хлеб!]]')
    text = text.replace('<konst:int_const_elem name="себе" />', '<konst:int_const_elem lu="себе" name="себе" role="себе" />')
    text = re.sub('<karp:text n=\"0\">Он \[\[любил её\]Action \[до конца\]\]до_конца\n          ]VP_до_конца и умер проговаривая её имя как\n          молитву\.</karp:text>', '<karp:text n="0">Он [любил_её]_Action [до]_до [конец]_конца и умер проговаривая её имя как молитву.</karp:text>', text)
    text = text.replace('<karp:e n="2" name="до+конца">до конца</karp:e>', '<karp:e n="2" name="до+конца.">до конца</karp:e>')
    text = re.sub('<karp:text n=\"0\">Учитель \[верил в невиновность ученика\]\n          до конца]до_конца ]VP_до_конца\. Он верил даже тогда,', '<karp:text n="0">Учитель [верил_в_невиновность_ученика]_Action [до]_до [конца]_конца. Он верил даже тогда,', text)
    text = text.replace('[an activity]Action', '[an_activity]_Action')
    text = re.sub('\[en\n          handling\]Action', '[en_handling]_Action', text)
    text = text.replace('<karp:e n="0" name="Situation">― Есть надо было', '<karp:e n="0" name="Situation">―Есть надо было')
    text = text.replace('[root [nsubj он] сочинял [obl [case по] [nummod несколько] стихотворений] [obl [case в] год.]]', '[root [nsubj он] сочинял [obl [case по] [nummod несколько] стихотворений] [obl [case в] год]]')
    text = text.replace('<karp:e n="7" name="Number">antall</karp:e>', '<karp:e n="7" name="Number">Antall</karp:e>')
    text = text.replace('<Sense id="konstruktikon-rus--как известно Cl">', '<Sense id="konstruktikon-rus--как_известно,_Cl">')
    text = re.sub('konstruksjon i norsk er ‘som kjent’\.<\/karp:text>\n        <\/definition>\n      <\/Sense>', 'konstruksjon i norsk er ‘som kjent’.</karp:text></definition><konst:int_const_elem lu="как" name="как" /><konst:int_const_elem lu="известно" name="известно" role="известно" /><konst:int_const_elem cat="Cl" name="Cl" role="Theme" /></Sense>', text)
    text = text.replace('[root [discourse [cc как] известно] Cl]', '[root [discourse [cc как] известно,] Cl]')
    text = text.replace('[root [discourse [cc как] известно] [nsubj он] мастер [obl [obj стихи] сочинять]]', '[root [discourse [cc как] известно,] [nsubj он] мастер [obl [obj стихи] сочинять]]')
    text = text.replace('konstruktikon-rus--NP_в_том_числе_(и)_NP', 'konstruktikon-rus--NP1_в_том_числе_(и)_NP2')
    text = re.sub('<konst:int_const_elem lu=\"в\" name=\"в\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"том\" \/>\n        <konst:int_const_elem lu=\"число\" name=\"числе\" \/>\n        <konst:int_const_elem lu=\"и\" name=\"и\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\" name=\"NP\"\n        role=\"Theme\" \/>\n        <konst:ext_const_elem cat=\"NP\" name=\"Referent\"\n        role=\"Referent\" \/>', '<konst:int_const_elem lu="в" name="в" /><konst:int_const_elem lu="то" name="том" /><konst:int_const_elem lu="число" name="числе" /><konst:int_const_elem lu="и" name="и" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP1" role="Theme" /><konst:ext_const_elem cat="NP" msd="NounType=Nom" name="NP2" role="Referent" />', text)
    text = text.replace('Он [любил_её]_Action [до]_до [конец]_конца и умер проговаривая её имя как молитву.', 'Он [любил_её]_Action [до]_до [конца]_конца и умер проговаривая её имя как молитву.')
    text = text.replace('<konst:int_const_elem cat=" ADV" lu="не" name="не" />', '<konst:int_const_elem cat="Particle" lu="не" msd="PartType=Neg" name="не" role="не" />')
    text = text.replace('konstruktikon-rus--по_Num-Acc_(NP-Gen)_NP-Gen', 'konstruktikon-rus--по_Num-Acc_(NP-Gen1)_NP-Gen2')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Gen\|Acc\"\n        name=\"NP-Gen\" role=\"Container\" \/>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumberType=Dat\"\n        name=\"Num-Acc\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"Prep\" lu=\"по\" name=\"по\"\n        role=\"по\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Gen\"\n        name=\"NP-Gen\" role=\"Theme\" \/>', '<konst:int_const_elem cat="NP" msd="NounType=Gen|Acc" name="NP-Gen1" role="Container" /><konst:int_const_elem cat="Num" msd="NumberType=Dat" name="Num-Acc" role="Number" /><konst:int_const_elem cat="Prep" lu="по" name="по" role="по" /><konst:int_const_elem cat="NP" msd="NounType=Gen" name="NP-Gen2" role="Theme" />', text)
    text = text.replace('konstruktikon-rus--Cl_с_тех_пор,_как_Cl', 'konstruktikon-rus--Cl1_с_тех_пор,_как_Cl2')
    text = re.sub('<konst:int_const_elem lu=\"с\" name=\"с\" \/>\n        <konst:int_const_elem lu=\"те\" name=\"тех\" \/>\n        <konst:int_const_elem lu=\"пора\" name=\"пор\" \/>\n        <konst:int_const_elem lu=\"как\" name=\"как\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Time\" \/>', '<konst:int_const_elem lu="с" name="с" /><konst:int_const_elem lu="те" name="тех" /><konst:int_const_elem lu="пора" name="пор" /><konst:int_const_elem lu="как" name="как" /><konst:int_const_elem cat="Cl" name="Cl1" role="Situation" /><konst:int_const_elem cat="Cl" name="Cl2" role="Time" />', text)
    text = re.sub('<konst:int_const_elem lu=\"вряд ли\" name=\"вряд ли\"\n        role=\"вряд_ли\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Event\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Action\" \/>\n        <konst:ext_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Agent\" \/>', '<konst:int_const_elem lu="вряд" name="вряд" role="вряд" /><konst:int_const_elem lu="ли" name="ли" role="ли" /><konst:int_const_elem cat="Cl" name="Cl" role="Event/Action" /><konst:ext_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom" role="Agent" />', text)
    text = text.replace('<karp:text n="4">?‘. I begge tilfeller foreslår taleren å', '<karp:text n="4">?’. I begge tilfeller foreslår taleren å')
    text = text.replace('konstruktikon-rus--Cl_не_только_Cl,_но_и_Cl', 'konstruktikon-rus--Cl1_не_только_Cl2,_но_и_Cl3')
    text = text.replace('[root Сl [advmod [advmod не] только] Cl, [conj [cc но [advmod и] Cl]]', '[root Сl [advmod [advmod не] только] Cl, [conj [cc но [advmod и] Cl.]]')
    text = re.sub('<konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" \/>\n        <konst:int_const_elem lu=\"только\" name=\"только\"\n        role=\"только\" \/>\n        <konst:int_const_elem lu=\"но\" name=\"но\" role=\"но\" \/>\n        <konst:int_const_elem lu=\"и\" name=\"и\" role=\"и\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Actant\" \/>', '<konst:int_const_elem cat="Cl" name="Cl1" role="Theme" /><konst:int_const_elem lu="не" name="не" role="не" /><konst:int_const_elem lu="только" name="только" role="только" /><konst:int_const_elem lu="но" name="но" role="но" /><konst:int_const_elem lu="и" name="и" role="и" /><konst:int_const_elem cat="Cl" name="Cl2" role="Situation" /><konst:int_const_elem cat="Cl" name="Cl3" role="Actant" />', text)
    text = text.replace('<konst:int_const_elem lu="в" name=" в" role="в" />', '<konst:int_const_elem lu="в" name="в" role="в" />')
    text = text.replace('[root [nsubj NP] пребывать [obl [case на/в] NP]] / [obl [case у] NP]]', '[root [nsubj NP] пребывать [obl [case на/в] NP] / [obl [case у] NP]]')
    text = text.replace('konstruktikon-rus--VP-Imper_не_VP-Imper_а_Cl', 'konstruktikon-rus--VP-Imper_не_VP-Imper,_а_Cl')
    text = text.replace('[root VP-Imper [parataxis [advmod не] VP-Imper] [conj [cc а] Cl]]', '[root VP-Imper [parataxis [advmod не] VP-Imper,] [conj [cc а] Cl]]')
    text = re.sub('<konst:int_const_elem cat="VP" msd="VerbType=Past"\n        name="VP" role="Action" \/>', '<konst:int_const_elem cat="VP" msd="VerbType=Past"\n        name="VP-Past" role="Action" />', text)
    text = text.replace('[root [nsubj он] [advmod не] сказал [obl [advmod ни] слова]] [obl [case за] [amod весь] вечер]]', '[root [nsubj он] [advmod не] сказал [obl [advmod ни] слова] [obl [case за] [amod весь] вечер]]')
    text = re.sub('<konst:int_const_elem lu="другой" msd="AdjType=Gen"\n        name="другой" role="другой" \/>', '<konst:int_const_elem lu="другой" msd="AdjType=Gen"\n        name="другой-Gen" role="другой" />', text)
    text = text.replace('konstruktikon-rus--сколько_бы_ни_VP-Past_Cl', 'konstruktikon-rus--сколько_бы_ни_VP-Past,_Cl')
    text = text.replace('[root [[advmod сколько] [aux бы] [advmod ни] [aux VP-Past]] Cl]', '[root [advmod сколько] [aux бы] [advmod ни] [aux VP-Past] Cl]')
    text = re.sub('<karp:text n="0">\[\[\[Как\]как \[это\]это \[у нас нет\n          альтернативного\n          искусства\?\]Situation\]как_это_Cl<\/karp:text>', '<karp:text n="0">[Как]_как [это]_это [у_нас_нет_альтернативного_искусства?]_Situation</karp:text>', text)
    text = text.replace('Устали).</karp:text>', 'устали).</karp:text>')
    text = text.replace('konstruktikon-rus--(как)_по_мне_(так)_Cl', 'konstruktikon-rus--(как)_по_мне,_(так)_Cl')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Pronominative\" msd=\"Type=Dat\"\n        name=\"PRONP-Dat\" role=\"Experiencer\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"Type=Dat\" name=\"NP-Dat\"\n        role=\"Theme\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Event\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Pronominative" msd="Type=Dat" name="PRONP-Dat" role="Experiencer" /><konst:int_const_elem cat="NP" msd="Type=Dat" name="NP-Dat" role="Theme" /><konst:int_const_elem cat="Adv" name="Adv" role="Evaluation" /></Sense>', text)
    text = text.replace('<konst:int_const_elem cat="Cl" name="Event" role="Event" />', '<konst:int_const_elem cat="Cl" name="Cl" role="Event" />')
    text = text.replace('konstruktikon-rus--ладно_(бы)_NP_Cl,_но_NP!', 'konstruktikon-rus--ладно_(бы)_NP1_Cl,_но_NP2!')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"ладно\" name=\"ладно\"\n        role=\"ладно\" \/>\n        <konst:int_const_elem lu=\"бы\" name=\"бы\" role=\"бы\" \/>\n        <konst:int_const_elem cat=\"NP\" name=\"NP1\" role=\"Theme\" \/><konst:int_const_elem cat=\"NP\" name=\"NP2\" role=\"Actant\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem lu=\"но\" name=\"но\" role=\"но\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="ладно" name="ладно" role="ладно" /><konst:int_const_elem lu="бы" name="бы" role="бы" /><konst:int_const_elem cat="NP" name="NP1" role="Actant" /><konst:int_const_elem cat="NP" name="NP2" role="Theme" /><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /><konst:int_const_elem lu="но" name="но" role="но" /></Sense>', text)
    text = text.replace('[parataxis [advmod уж] кому-кому], [mark а] [obl ему] [nsubj я] [advmod точно] нужна]', '[parataxis [advmod уж] кому-кому, [mark а] [obl ему] [nsubj я] [advmod точно] нужна]')
    text = text.replace('<konst:int_const_elem lu="был" name="быть" role="быть" />', '<konst:int_const_elem lu="был" name="быть-Past" role="быть" />')
    text = re.sub('<konst:int_const_elem lu="этот" msd="NounType=Nom"\n        name="этот" role="этот" \/>', '<konst:int_const_elem lu="этот" msd="NounType=Nom" name="этот-Nom" role="этот" />', text)
    text = text.replace('[root [advmod неужели] [advmod не] VP]', '[root [advmod неужели] [advmod не] VP?]')
    text = text.replace('konstruktikon-rus--не_грех_и_VP-Perf.Inf', 'konstruktikon-rus--не_грех_и_VP-Inf')
    text = text.replace('konstruktikon-rus--Adv-то_как_Cl!', 'konstruktikon-rus--Adv -то_как_Cl!')
    text = text.replace('"konstruktikon-rus--к_чему_Cl"', '"konstruktikon-rus--к_чему_Cl?"')
    text = text.replace('[root [obl [case к] чему] Cl]', '[root [obl [case к] чему] Cl?]')
    text = text.replace('<konst:int_const_elem cat="Action" name="Action"', '<konst:int_const_elem cat="Action" name="Cl"')
    text = text.replace('konstruktikon-rus--хоть_Int', 'konstruktikon-rus--хоть_SCONJ')
    text = text.replace('[root [obj что] [advmod ни] говори(те), [conj ([cc а]) Cl]', '[root [obj что] [advmod ни] говори(те), [conj [(cc а)] Cl]')
    text = re.sub('<karp:text n="0">С экономикой сегодня,<\/karp:text>\n          <karp:e n="1" name="что\+ни\+говори\(те\)\+\(а\)\+Cl">\n            <karp:e n="0" name="что">Что<\/karp:e>', '<karp:text n="0">С экономикой сегодня,</karp:text><karp:e n="1" name="что+ни+говори(те)+(а)+Cl"><karp:e n="0" name="что">что</karp:e>', text)
    text = text.replace('konstruktikon-rus--ходить_в_NP-Loc.Plur', 'konstruktikon-rus--ходить_в_NP-Loc')
    text = text.replace('[root [advmod ещё] [advmod (и)] [nsubj учительница] называется]', '[root [advmod ещё] [advmod (и)] [nsubj учительница] называется!]')
    text = text.replace('[root [nsubj это] [cop было] [advmod не] болото, [conj [cc а] болотище]!]', '[root [nsubj это] [cop было] [advmod не] болото, [conj [cc а] болотище!]]')
    text = text.replace('[root [dep хоть] VP] [conj [cc no/a] Cl]]', '[root [dep хоть] VP [conj [cc но/a] Cl]]')
    text = text.replace('[root [dep хоть] умри], [conj [cc а] [advmod завтра] должен [cop быть] [obl [case на] работе] [obl [advmod рано] [advmod утром]', '[root [dep хоть] умри, [conj [cc а] [advmod завтра] должен [cop быть] [obl [case на] работе] [obl [advmod рано] [advmod утром]]]')
    text = text.replace('konstruktikon-rus--принять-Past_NP-Acc_за_NP-Acc', 'konstruktikon-rus--принять-Past_NP-Acc1_за_NP-Acc2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"принять\" msd=\"VerbType=Past\"\n        name=\"принять-Past\" role=\"принять\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"за\" name=\"за\" role=\"за\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Prototype\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="принять" msd="VerbType=Past" name="принять-Past" role="принять" /><konst:int_const_elem cat="NP" msd="NounType=Acc" name="NP-Acc1" role="Theme" /><konst:int_const_elem lu="за" name="за" role="за" /><konst:int_const_elem cat="NP" msd="NounType=Acc" name="NP-Acc2" role="Prototype" /></Sense>', text)
    text = text.replace('[root [obl [case на] [ ярмарке] [nsubj чего] [advmod только] нет!]', '[root [obl [case на] [ярмарке] [nsubj чего] [advmod только] нет!]]')
    text = re.sub('<karp:e n=\"8\" name=\"нет\">нет\!<\/karp:e>\n            <karp:text n=\"9\">-<\/karp:text>\n            <karp:g n=\"10\" \/>\n            <karp:text n=\"11\" \/>\n          <\/karp:e>', '<karp:e n="8" name="нет">нет!</karp:e><karp:text n="9" /></karp:e>', text)
    text = text.replace('konstruktikon-rus--грех_не_VP-Perf.Inf', 'konstruktikon-rus--грех_не_VP-Inf')
    text = text.replace('konstruktikon-rus--S_ещё_бы_(S)!', 'konstruktikon-rus--S1_ещё_бы_(S2)!')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Adv\" lu=\"ещё\" name=\"ещё\"\n        role=\"ещё\" \/>\n        <konst:int_const_elem lu=\"бы\" name=\"бы\" role=\"бы\" \/>\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Theme\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Adv" lu="ещё" name="ещё" role="ещё" /><konst:int_const_elem lu="бы" name="бы" role="бы" /><konst:int_const_elem cat="Clause" name="S1" role="Situation" /><konst:int_const_elem cat="Clause" name="S2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--(Cl)_разве_что/только_Cl', 'konstruktikon-rus--(Cl1)_разве_что/только_Cl2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"разве\" name=\"разве\"\n        role=\"разве\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Limitation\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="разве" name="разве" role="разве" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem cat="Cl" name="Cl1" role="Situation" /><konst:int_const_elem cat="Cl" name="Cl2" role="Limitation" /><konst:int_const_elem lu="только" name="только" role="только" /></Sense>', text)
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"только\" name=\"только\"\n        role=\"только\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Genitive\"\n        name=\"NP-Gen\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"NP-Dat\" role=\"Experiencer\" \/>\n        <konst:int_const_elem lu=\"ещё\" name=\"ещё\" role=\"ещё\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="только" name="только" role="только" /><konst:int_const_elem cat="NP" msd="NounType=Genitive" name="NP-Gen" role="Theme" /><konst:int_const_elem lu="не" name="не" role="не" /><konst:int_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat" role="Experiencer" /><konst:int_const_elem lu="ещё" name="ещё" role="ещё" /><konst:int_const_elem lu="хватало" name="хватало" role="хватало" /></Sense>', text)
    text = text.replace('konstruktikon-rus--не_то_XP_не_то_XP', 'konstruktikon-rus--не_то_XP,_не_то_XP')
    text = text.replace('konstruktikon-rus--не_то_XP,_не_то_XP', 'konstruktikon-rus--не_то_XP1,_не_то_XP2')
    text = re.sub('<konst:int_const_elem cat="XP" name="XP" role="Theme" \/>\n        <konst:int_const_elem cat="XP" name="XP" role="Actant" \/>', '<konst:int_const_elem cat="XP" name="XP1" role="Theme" /><konst:int_const_elem cat="XP" name="XP2" role="Actant" />', text)
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nominative\"\n        name=\"Agent\" role=\"Agent\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Reflexive\"\n        name=\"VP\" role=\"Action\" \/>\n        <konst:int_const_elem lu=\"над\" name=\"над\" role=\"над\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Instrumental\"\n        name=\"Patient\" role=\"Patient\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Nominative" name="NP-Nom" role="Agent" /><konst:int_const_elem cat="VP" msd="VerbType=Reflexive" name="над-VP-ся" role="Action" /><konst:int_const_elem lu="над" name="над" role="над" /><konst:int_const_elem cat="NP" msd="NounType=Instrumental" name="NP-Ins" role="Patient" /></Sense>', text)
    text = text.replace('<karp:e n="6" name="Patient">новеньком</karp:e>', '<karp:e n="6" name="Patient">новеньким</karp:e>')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Condition\" \/>\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"то\" role=\"то\" \/>\n        <konst:int_const_elem lu=\"с\" name=\"с\" role=\"с\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Ins\"\n        name=\"NP-Ins\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"быть\" name=\"быть-Fut\"\n        role=\"быть\" \/>\n        <konst:int_const_elem lu=\"иметь\" name=\"иметь\"\n        role=\"иметь\" \/>\n        <konst:int_const_elem lu=\"дело\" msd=\"Type=Acc\" name=\"дело\"\n        role=\"дело\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Cl" name="Cl" role="Condition" /><konst:int_const_elem lu="не" name="не" role="не" /><konst:int_const_elem lu="то" name="то" role="то" /><konst:int_const_elem lu="с" name="с" role="с" /><konst:int_const_elem cat="NP" msd="NounType=Ins" name="NP-Ins" role="Theme" /><konst:int_const_elem lu="быть" name="быть-Fut" role="быть" /><konst:int_const_elem lu="иметь" name="иметь" role="иметь" /><konst:int_const_elem lu="дело" msd="Type=Acc" name="дело" role="дело" /><konst:int_const_elem lu="а" name="а" /></Sense>', text)
    text = re.sub('<konst:int_const_elem lu="знать" name="знает"\n        role="знает" \/>', '<konst:int_const_elem lu="знать" name="знать" role="знает" />', text)
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"чтобы\" name=\"чтобы\"\n        role=\"чтобы\" \/>\n        <konst:int_const_elem cat=\"Pronoun\" name=\"Pron\"\n        role=\"Experiencer\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Past\"\n        name=\"VP-Past\" role=\"Action\" \/>\n        <konst:int_const_elem lu=\"чтоб\" name=\"чтоб\" role=\"чтоб\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="чтоб(ы)" name="чтоб(ы)" role="чтоб(ы)" /><konst:int_const_elem cat="Pronoun" name="Pron" role="Experiencer" /><konst:int_const_elem cat="VP" msd="VerbType=Past" name="VP-Past" role="Action" /><konst:int_const_elem lu="чтоб" name="чтоб" role="чтоб" /></Sense>', text)
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"VP\" lu=\"стоить\" name=\"стоить\"\n        role=\"стоить\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Perf\"\n        name=\"VP-Perf\" role=\"Action\" \/>\n        <konst:int_const_elem lu=\"как\" name=\"как\" role=\"как\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Event\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="VP" lu="стоить" name="стоить" role="стоить" /><konst:int_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat" role="Experiencer" /><konst:int_const_elem cat="VP" msd="VerbType=Perf" name="VP-Perf" role="Action" /><konst:int_const_elem lu="как" name="как" role="как" /><konst:int_const_elem cat="Cl" name="Cl" role="Event" /></Sense>', text)
    text = text.replace('[root [nsubj я] пошел [aux было] [obl [case на] работу]], [conj [cc но] передумал]]', '[root [nsubj я] пошел [aux было] [obl [case на] работу], [conj [cc но] передумал]]')
    text = text.replace('[root [nsubj ты] не поедешь?] [dep Нет так нет.]', '[root [nsubj ты] не поедешь? [dep Нет так нет.]]')
    text = re.sub('остаться\?<\/karp:e>\n            <karp:text n="1" \/>\n            <karp:e n="2" name="нет">нет<\/karp:e>', 'остаться?</karp:e><karp:text n="1" /><karp:e n="2" name="нет">Нет</karp:e>', text)
    text = text.replace('[root [nsubj [amod летние] пожары] [advmod почти] уничтожили [advmod и] [fixed без] [fixed того]]] [obj [amod небогатый] урожай]]', '[root [nsubj [amod летние] пожары] [advmod почти] уничтожили [advmod и] [fixed без] [fixed того] [obj [amod небогатый] урожай]]')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Participant\" \/>\n        <konst:int_const_elem lu=\"за\" name=\"за\" role=\"за\" \/>\n        <konst:int_const_elem lu=\"свой\" name=\"своё\" role=\"своё\" \/>\n        <konst:int_const_elem lu=\"опять\" name=\"опять\"\n        role=\"опять\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom" role="Participant" /><konst:int_const_elem lu="за" name="за" role="за" /><konst:int_const_elem lu="свой" name="своё" role="своё" /><konst:int_const_elem lu="опять" name="опять" role="опять" /><konst:int_const_elem lu="всё" name="всё" role="всё" /></Sense>', text)
    text = text.replace('name="NP-Acc" role="Number" />', 'name="Num-Acc" role="Number" />')
    text = text.replace('<karp:e n="0" name="Action">они</karp:e>', '<karp:e n="0" name="Agent">они</karp:e>')
    text = text.replace('<karp:e n="1" name="Theme">действия.</karp:e>', '<karp:e n="1" name="Theme">действия</karp:e>')
    text = text.replace('konstruktikon-rus--ходить_слух_что_Cl', 'konstruktikon-rus--ходить_слух,_что_Cl')
    text = text.replace('konstruktikon-rus--где_бы_ни_VP-Past_Cl', 'konstruktikon-rus--где_бы_ни_VP-Past,_Cl')
    text = text.replace('name="V-Pst" role="Action" />', 'name="V-Past" role="Action" />')
    text = text.replace('name="Experiencer" role="Pron-Gen" />', 'name="Pron-Gen" role="Experiencer" />')
    text = text.replace('konstruktikon-rus--бросить-Imper_VP-Imp.Inf', 'konstruktikon-rus--бросать-Imper_VP-Imp.Inf')
    text = text.replace('[root [obl на] [amod его] месте] [nsubj я] [aux бы] поступила [obl [case в] [amod другой] университет]]', '[root [obl на] [amod его] месте [nsubj я] [aux бы] поступила [obl [case в] [amod другой] университет]]')
    text = re.sub('<feat att=\"structure\"\n        val=\"\[root \[obl \[case на\] \[amod Pron-Gen\] месте\] Cl\] \[obl \[case на\] месте \[nmod NP-Gen\]\] Cl\]\" \/>', '<feat att="structure" val="[root [obl [case на] [amod Pron-Gen] месте] Cl]"/><feat att="structure" val="[root [obl [case на] месте [nmod NP-Gen]] Cl]"/>', text)
    text = text.replace('konstruktikon-rus--VP-Past_бы_,Cl_бы', 'konstruktikon-rus--VP-Past_бы,_Cl_бы')
    text = text.replace('[root VP-Past [бы], [parataxis Cl [бы]]', '[root VP-Past бы, [parataxis Cl бы]]')
    text = re.sub('<karp:e n="4" name="Situation">\n              <karp:text n="0">он<\/karp:text>\n              <karp:e n="1" name="бы">бы<\/karp:e>\n              <karp:text n="2">тебя и до дома проводил\.<\/karp:text>\n            <\/karp:e>', '<karp:text n="0">он</karp:text><karp:e n="1" name="бы">бы</karp:e><karp:text n="2">тебя и до дома проводил.</karp:text>', text)
    text = re.sub('<karp:e n="4" name="Situation">\n              <karp:text n="0">сейчас<\/karp:text>\n              <karp:e n="1" name="бы">бы<\/karp:e>\n              <karp:text n="2">согрелись\.<\/karp:text>\n            <\/karp:e>', '<karp:text n="0">сейчас</karp:text><karp:e n="1" name="бы">бы</karp:e><karp:text n="2">согрелись.</karp:text>', text)
    text = re.sub('<karp:e n="4" name="Situation">\n              <karp:text n="0">голова<\/karp:text>\n              <karp:e n="1" name="бы">бы<\/karp:e>\n              <karp:text n="2">не болела\.<\/karp:text>\n            <\/karp:e>', '<karp:text n="0">голова</karp:text><karp:e n="1" name="бы">бы</karp:e><karp:text n="2">не болела.</karp:text>', text)
    text = text.replace('konstruktikon-rus--каждый раз VP, (когда Cl)', 'konstruktikon-rus--каждый_раз_VP,_(когда_Cl)')
    text = re.sub('<karp:text n=\"4\">обязательно происходит при выполнении\n          условия, содержащегося в<\/karp:text>\n          <karp:e n=\"5\" name=\"Cl\.\">клаузе<\/karp:e>\n          <karp:text n=\"6\" \/>\n        <\/definition>\n      <\/Sense>', '<karp:text n="4">обязательно происходит при выполнении условия, содержащегося в</karp:text><karp:e n="5" name="Cl.">клаузе</karp:e><karp:text n="6" /></definition><konst:int_const_elem lu="каждый" name="каждый" role="каждый" /><konst:int_const_elem lu="раз" name="раз" role="раз" /><konst:int_const_elem cat="VP" name="VP" role="Action" /><konst:int_const_elem lu="когда" name="когда" role="когда" /><konst:int_const_elem name="Cl" role="Situation" /></Sense>', text)
    text = text.replace('[root VP [[advmod [amod каждый] раз] [xcomp [advmod когда] Cl]]', '[root VP [advmod [amod каждый] раз] [xcomp [advmod когда] Cl]]')
    text = text.replace('[root [[advmod [amod каждый] раз] VP [xcomp [advmod когда] Cl]]', '[root [advmod [amod каждый] раз] VP [xcomp [advmod когда] Cl]]')
    text = text.replace('[root [[advmod [amod каждый] раз] улыбаюсь [xcomp [advmod когда] вижу [obj её]]]', '[root [advmod [amod каждый] раз] улыбаюсь [xcomp [advmod когда] вижу [obj её]]]')
    text = text.replace('<karp:text n="4">о том</karp:text>', '<karp:text n="4">о том,</karp:text>')
    text = text.replace('konstruktikon-rus--NP-Nom_самый_что_ни_на_есть_NP-Nom', 'konstruktikon-rus--NP-Nom1_самый_что_ни_на_есть_NP-Nom2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"самый\" name=\"самый\"\n        role=\"самый\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" \/>\n        <konst:int_const_elem lu=\"ни\" name=\"ни\" role=\"ни\" \/>\n        <konst:int_const_elem lu=\"на\" name=\"на\" role=\"на\" \/>\n        <konst:int_const_elem cat=\"Verb\" lu=\"быть\" name=\"есть\"\n        role=\"есть\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Evaluation\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Agent\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="самый" name="самый" role="самый" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem lu="ни" name="ни" role="ни" /><konst:int_const_elem lu="на" name="на" role="на" /><konst:int_const_elem cat="Verb" lu="быть" name="есть" role="есть" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Evaluation" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Agent" /></Sense>', text)
    text = re.sub('<feat att=\"structure\"\n        val=\"\[root \[nsubj ты \[amod самый\]\] что \[fixed ни \[fixed на \[fixed есть\]\]\] \[nsubj \[amod умный\] человек!\]\]\" \/>\n        <feat att=\"structure\"\n        val=\"\[root \[obl нам\] удалось \[nsubj пообщаться \[obl \[case с\] \[amod самым \[advmod что \[fixed ни \[fixed на \[fixed есть\]\]\]\] \[amod настоящим\] генетиком!\]\]\" \/>\n        <feat att=\"structure\"\n        val=\"\[root \[nsubj организация\] создается \[obl \[amod \[amod самым \[obj что \[fixed ни \[fixed на \[fixed есть\]\]\]\]\] демократичным\] путем\]\]\" \/>\n        <feat att=\"structure\"\n        val=\"\[root \[nsubj NP-Nom\] \[amod самый\] что \[fixed ни \[fixed на fixed есть\]\]\] \[nsubj NP-Nom\]\]\" \/>', '<feat att="structure" val="[root [nsubj ты [amod самый]] что [fixed ни [fixed на [fixed есть]]] [nsubj [amod умный] человек!]]" /><feat att="structure" val="[root [obl нам] удалось [nsubj пообщаться [obl [case с] [amod самым [advmod что [fixed ни [fixed на [fixed есть]]]] [amod настоящим] генетиком!]]" /><feat att="structure" val="[root [nsubj организация] создается [obl [amod [amod самым [obj что [fixed ни [fixed на [fixed есть]]]]] демократичным] путем]]" />', text)
    text = text.replace('"[parataxis вроде [fixed бы]] [nsubj он] обещал [xcomp прийти]]"', '"[root [parataxis вроде [fixed бы]] [nsubj он] обещал [xcomp прийти]]"')
    text = text.replace('"[parataxis вроде [fixed бы]] XP]"', '"[root [parataxis вроде [fixed бы]] XP]"')
    text = text.replace('konstruktikon-rus--переделать_NP-Acc_под_NP-Acc', 'konstruktikon-rus--переделать_NP-Acc1_под_NP-Acc2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"переделать\" name=\"переделать\"\n        role=\"переделать\" \/>\n        <konst:int_const_elem lu=\"под\" name=\"под\" role=\"под\" \/>\n        <konst:int_const_elem cat=\"NP\" gfunc=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Patient\" \/>\n        <konst:int_const_elem cat=\"NP\" gfunc=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Theme\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="переделать" name="переделать" role="переделать" /><konst:int_const_elem lu="под" name="под" role="под" /><konst:int_const_elem cat="NP" gfunc="NounType=Acc" name="NP-Acc1" role="Patient" /><konst:int_const_elem cat="NP" gfunc="NounType=Acc" name="NP-Acc2" role="Theme" /></Sense>', text)
    text = text.replace('<konst:int_const_elem lu="a" name="a" />', '<konst:int_const_elem lu="а" name="а" />')
    text = text.replace('[root пришёл [advmood-таки!]', '[root пришёл [advmood -таки!]')
    text = text.replace('[root VP-Past [advmood-таки!]', '[root VP-Past [advmood -таки!]')
    text = re.sub('	', '    ', text)
    text = re.sub('<karp:example>\n          <karp:text n=\"0\">Однако капитан<\/karp:text>\n          <karp:e n=\"1\" name=\"VP-Past-таки!\">\n            <karp:e n=\"0\" name=\"Action\">дал<\/karp:e>\n            <karp:text n=\"1\" \/>\n            <karp:e n=\"2\" name=\"таки\">-таки<\/karp:e>\n            <karp:g n=\"3\" \/>\n            <karp:text n=\"4\" \/>\n          <\/karp:e>\n          <karp:text n=\"2\">мне деньги, велел спрятать\n          шкатулку\.<\/karp:text>\n        <\/karp:example>', '', text)
    text = text.replace('name="NP-Dat.Sg" role="Theme" />', 'name="NP-Dat" role="Theme" />')
    text = text.replace('konstruktikon-rus--Вот_VP-Fut,_и_VP-Fut', 'konstruktikon-rus--Вот_VP-Fut1,_и_VP-Fut2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"вот\" name=\"вот\" role=\"вот\" \/>\n        <konst:int_const_elem lu=\"и\" name=\"и\" role=\"и\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Inf\"\n        name=\"VP-Inf\" role=\"Action\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Inf\"\n        name=\"VP-Inf\" role=\"Event\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="вот" name="вот" role="вот" /><konst:int_const_elem lu="и" name="и" role="и" /><konst:int_const_elem cat="VP" msd="VerbType=Fut" name="VP-Fut1" role="Action" /><konst:int_const_elem cat="VP" msd="VerbType=Fut" name="VP-Fut2" role="Event" /></Sense>', text)
    text = text.replace('konstruktikon-rus--кроме_того_XP', 'konstruktikon-rus--кроме_того,_XP')
    text = text.replace('[root [cc а] [nsubj он] [dep как] начал [xcomp кричать]!]', '[root [cc а] [nsubj он] [dep как] начал [xcomp кричать!]]')
    text = text.replace('[root [dep как] начать [xcomp VP-Inf]!]', '[root [dep как] начать [xcomp VP-Inf!]]')
    text = text.replace('konstruktikon-rus--NP-Nom.Plur_в_один_голос-Acc_VP', 'konstruktikon-rus--NP-Nom.Plur_в_один_голос_VP')
    text = re.sub('<karp:e n=\"2\" name=\"Situation\">\n              <karp:e n=\"0\" name=\"тем\+не\+менее,\">тем не\n              менее<\/karp:e>\n              <karp:text n=\"1\">появляются и проекты, которые\n              удаётся осуществить<\/karp:text>\n            <\/karp:e>', '<karp:e n="0" name="тем+не+менее,">тем не менее</karp:e><karp:e n="1">появляются и проекты, которые удаётся осуществить</karp:e>', text)
    text = re.sub('<karp:e n=\"1\" name=\"Situation\">\n              <karp:e n=\"0\" name=\"тем\+не\+менее,\">тем не\n              менее<\/karp:e>\n              <karp:text n=\"1\">выступающих оказалось более десяти\n              человек<\/karp:text>\n            <\/karp:e>', '<karp:e n="0" name="тем+не+менее,">тем не менее</karp:e><karp:text n="1">выступающих оказалось более десяти человек</karp:text>', text)
    text = re.sub('<karp:e n=\"2\" name=\"Situation\">\n              <karp:text n=\"0\" \/>\n              <karp:e n=\"1\" name=\"тем\+н\е\+менее,\">тем не\n              менее<\/karp:e>\n              <karp:text n=\"2\">волновала тема кризиса\n              художника<\/karp:text>\n            <\/karp:e>', '<karp:text n="0" /><karp:e n="1" name="тем+не+менее,">тем не менее</karp:e><karp:e n="2" name="Situation">волновала тема кризиса художника</karp:e>', text)
    text = text.replace('[root [obl [case за] кого] [nsubj NP-Nom] [obj NP-Acc] принимать?] S', '[root [obl [case за] кого] [nsubj NP-Nom] [obj NP-Acc] принимать? S]')
    text = text.replace('[root [obl [case за] кого] [nsubj он] [obj меня] принимает?] Я никогда не списываю', '[root [obl [case за] кого] [nsubj он] [obj меня] принимает? Я никогда не списываю]')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Inf\"\n        name=\"VP\" role=\"Action\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Inf\"\n        name=\"VP-Inf\" role=\"Action\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" \/>\n        <konst:int_const_elem lu=\"бы\" name=\"бы\" role=\"бы\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"то\" role=\"то\" \/>\n        <konst:int_const_elem lu=\"стать\" name=\"стало\"\n        role=\"стало\" \/>\n        <konst:int_const_elem lu=\"ни\" name=\"ни\" role=\"ни\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="VP" msd="VerbType=Inf" name="VP" role="Action" /><konst:int_const_elem cat="VP" msd="VerbType=Inf" name="VP-Inf" role="Action" /><konst:int_const_elem lu="в" name="во" role="во" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem lu="бы" name="бы" role="бы" /><konst:int_const_elem lu="то" name="то" role="то" /><konst:int_const_elem lu="стать" name="стало" role="стало" /><konst:int_const_elem lu="ни" name="ни" role="ни" /></Sense>', text)
    text = text.replace('[root VP-Inf] [obl [case во] что [fixed бы [fixed то [fixed ни [fixed стало]]]]]]', '[root VP-Inf [obl [case во] что [fixed бы [fixed то [fixed ни [fixed стало]]]]]]')
    text = text.replace('[root куда] [obl Оле] [obl [case до] [amod моей] дочки]]. Моя дочка ведь такая красивая!', '[root куда [obl Оле] [obl [case до] [amod моей] дочки.] Моя дочка ведь такая красивая!]')
    text = text.replace('<karp:e n="2" name="Goal">им</karp:e>', '<karp:e n="2" name="Experiencer">им</karp:e>')
    text = text.replace('<karp:e n="1" name="experiencer">кто-то</karp:e>', '<karp:e n="1" name="Experiencer">кто-то</karp:e>')
    text = text.replace('[root [obl [amod такому] человеку, [appos [case как] он],] [advmod не] стыдно [csubj признаться [obl [case в] [amod своей] неправоте]]', '[root [obl [amod такому] человеку, [appos [case как] он,]] [advmod не] стыдно [csubj признаться [obl [case в] [amod своей] неправоте]]')
    text = text.replace('[root [dep [amod такой] NP, [appos [case как] NP-Nom],] Cl]', '[root [dep [amod такой] NP, [appos [case как] NP-Nom,]] Cl]')
    text = text.replace('[root [parataxis как не]VP-Inf]', '[root [parataxis как не] VP-Inf]')
    text = text.replace('[root [advmod [amod тем] временем] [nsubj директор] покинул [obj здание] ]', '[root [advmod [amod тем] временем] [nsubj директор] покинул [obj здание]]')
    text = text.replace('[root Cl [conj [cc а] [advmod [amod тем] временем] Cl ]]', '[root Cl [conj [cc а] [advmod [amod тем] временем] Cl]]')
    text = text.replace('Сначала― ', 'Сначала ― ')
    text = text.replace('затем― ', 'затем ― ')    
    text = text.replace('потом―', 'потом ―')
    text = text.replace('[root [nsubj я] приду [advmod где-то] [obl [case в] восем вечера]]', '[root [nsubj я] приду [advmod где-то] [obl [case в] восемь вечера]]')
    text = text.replace('konstruktikon-rus--что_бы_ни_VP-Past_Cl', 'konstruktikon-rus--что_бы_ни_VP-Past,_Cl')
    text = text.replace('konstruktikon-rus--едва_(ли)_не_ХP', 'konstruktikon-rus--едва_(ли)_не_XP')
    text = text.replace('<konst:int_const_elem cat="XP" name="XP" role="Standard" />', '<konst:int_const_elem cat="XP" name="XP" role="Standard" />')
    text = text.replace('<karp:e n="8" name="ли.">"ли"</karp:e>', '<karp:e n="8" name="ли">"ли"</karp:e>')
    text = text.replace('konstruktikon-rus--того_и_гляди_VP-Perf', 'konstruktikon-rus--того_и_гляди_VP')
    text = text.replace('<karp:e n="2" name="Action">лучше</karp:e>', '<karp:e n="2" name="лучше">лучше</karp:e>')
    text = text.replace('konstruktikon-rus--что_Pron-Dat_NP-Nom_если_Cl?', 'konstruktikon-rus--что_Pron-Dat_NP-Nom,_если_Cl?')
    text = text.replace('konstruktikon-rus--не_то_чтобы_Cl_а/но_Cl', 'konstruktikon-rus--не_то_чтобы_Cl,_а/но_Cl')
    text = text.replace('konstruktikon-rus--не_то_чтобы_Cl,_а/но_Cl', 'konstruktikon-rus--не_то_чтобы_Cl1,_а/но_Cl2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"не\" name=\"не\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"то\" \/>\n        <konst:int_const_elem lu=\"чтобы\" name=\"чтобы\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Theme\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"но\" name=\"но\" \/>\n        <konst:int_const_elem lu=\"а\" name=\"а\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Event\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="не" name="не" /><konst:int_const_elem lu="то" name="то" /><konst:int_const_elem lu="чтобы" name="чтобы" /><konst:int_const_elem cat="Cl" name="Cl1" role="Theme" /><konst:int_const_elem lu="но" name="но" /><konst:int_const_elem lu="а" name="а" /><konst:int_const_elem cat="Cl" name="Cl2" role="Event" /></Sense>', text)
    text = text.replace('konstruktikon-rus--даваться-Past_Pron-Dat_этот_NP-Nom!', 'konstruktikon-rus--даваться_Pron-Dat_этот_NP-Nom!')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat="Cl" name="Cl"\n        role="Situation" \/>\n        <konst:int_const_elem lu="если" name="если" role="если" \/>\n        <konst:int_const_elem \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /><konst:int_const_elem lu="если" name="если" role="если" /><konst:int_const_elem cat="Pronoun" lu="ты/вы" name="Pron-2"/><konst:int_const_elem cat="Part" lu="не" name="не" role="не" /><konst:int_const_elem cat="Adverb" name="Adv" role="Property" /></Sense>', text)
    text = text.replace('konstruktikon-rus--ничто_иное,_кроме,_NP-Gen_Cl', 'konstruktikon-rus--ничто_иное,_кроме_NP-Gen,_Cl')
    text = text.replace('konstruktikon-rus--смотреть-Imper,_не_VP-Imper', 'konstruktikon-rus--смотреть,_не_VP-Imper')
    text = text.replace('konstruktikon-rus--NP-Nom_VP-VP_а_не_Cl', 'konstruktikon-rus--NP-Nom_VP-VP,_а_не_Cl')
    text = text.replace('[root [nsubj NP-Nom] VP-VP [conj [cc а] [advmod не] Cl]]', '[root [nsubj NP-Nom] VP-VP, [conj [cc а] [advmod не] Cl]]')
    text = re.sub('<konst:int_const_elem lu=\"будет\" name=\"будет\"\n        role=\"будет\" \/>\n        <konst:int_const_elem cat=\"VP\" msd=\"VerbType=Imp\.Past\"\n        name=\"VP-Past\" role=\"Action\" \/>\n      <\/Sense>', '<konst:int_const_elem lu="будет" name="будет" role="будет" /><konst:int_const_elem cat="VP" msd="VerbType=Imp.Past" name="по-VP-Past" role="Action" /></Sense>', text)
    text = text.replace('konstruktikon-rus--когда_бы_ни_VP-Past_Cl', 'konstruktikon-rus--когда_бы_ни_VP-Past,_Cl')
    text = re.sub('<\/definition>\n        <konst:int_const_elem name=\"какой\" role=\"какой\" \/>\n        <konst:int_const_elem cat=\"XP\" name=\"XP\" role=\"Theme\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem name="какой" role="какой" /><konst:int_const_elem cat="XP" name="XP" role="Theme" /><konst:int_const_elem lu="там" name="там" role="там" /></Sense>', text)
    text = text.replace('konstruktikon-rus--сегодня_ХP,_завтра_XP', 'konstruktikon-rus--сегодня_XP,_завтра_XP')
    text = text.replace('konstruktikon-rus--NP-Nom_VP_NP-Ins.Plur_NP-Acc', 'konstruktikon-rus--NP-Nom_VP-Imp_NP-Ins.Plur_NP-Acc')
    text = text.replace('konstruktikon-rus--NP_и_так_VP_(а)_Cl', 'konstruktikon-rus--NP_и_так_VP,_(а)_Cl')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"умирать\" name=\"умираю\"\n        role=\"умираю\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"State\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="умирать" name="умирать-Pres.1.Sing" role="умираю" /><konst:int_const_elem cat="Cl" name="Cl" role="State" /></Sense>', text)
    text = text.replace('konstruktikon-rus--не_что_иное_как,_NP-Nom', 'konstruktikon-rus--не_что_иное,_как_NP-Nom')
    text = re.sub('<karp:e n="1" name="Action">действие\.<\/karp:e>\n          <karp:g n="2" \/>', '<karp:e n="1" name="Action">действие</karp:e><karp:g n="2" />', text)
    text = text.replace('konstruktikon-rus--раз_(уж)_Cl,_(то)_Cl', 'konstruktikon-rus--раз_(уж)_Cl1,_(то)_Cl2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"раз\" name=\"раз\" role=\"раз\" \/>\n        <konst:int_const_elem lu=\"уж\" name=\"уж\" role=\"уж\" \/>\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Action\" \/>\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Condition\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"то\" role=\"то\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="раз" name="раз" role="раз" /><konst:int_const_elem lu="уж" name="уж" role="уж" /><konst:int_const_elem cat="Clause" name="Cl2" role="Action" /><konst:int_const_elem cat="Clause" name="Cl1" role="Condition" /><konst:int_const_elem lu="то" name="то" role="то" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP-Nom_не_в_силах_VP-Inf', 'konstruktikon-rus--NP-Nom_не_в_силах_VP-Inf.Perf')
    text = text.replace('<karp:e n="7" name="Actant">лет</karp:e>', '<karp:e n="7" name="Actant,">лет</karp:e>')
    text = text.replace('[root [advmod да] [nsubj ты] влюблена [obl [case в] него]! - [dep Вот ещё!]]', '[root [advmod да] [nsubj ты] влюблена [obl [case в] него!] - [dep Вот ещё!]]')
    text = text.replace('<karp:e n="4" name="вот">Вот</karp:e>', '<karp:e n="4" name="вот">вот</karp:e>')
    text = text.replace('<karp:e n="1" name="Situation">предложение или', '<karp:e n="1" name="Situation">предложения или')
    text = text.replace('msd="VerbType=Perfective, Fut" name="VP-Fut.Perf!"', 'msd="VerbType=Perfective=Fut" name="VP-Fut.Perf"')
    text = re.sub('<karp:text n=\"12\">!<\/karp:text>\n          <\/karp:e>\n          <karp:g n=\"1\" \/>\n          <karp:text n=\"2\">!<\/karp:text>', '</karp:e><karp:g n="1" /><karp:text n="2">!</karp:text>', text)
    text = text.replace('konstruktikon-rus--чем_NP-Nom_не_NP-Nom?', 'konstruktikon-rus--чем_NP-Nom1_не_NP-Nom2?')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Theme\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Property\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"чем\" role=\"чем\" \/>\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Theme" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Property" /><konst:int_const_elem lu="что" name="чем" role="чем" /><konst:int_const_elem lu="не" name="не" role="не" /></Sense>', text)
    text = text.replace('[root Cl] [obl [case с] тем [mark чтобы] [advcl VP]]]', '[root Cl [obl [case с] тем [mark чтобы] [advcl VP]]]')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Part\" lu=\"не\" name=\"не\"\n        role=\"не\" \/>\n        <konst:int_const_elem lu=\"то\" name=\"то\" role=\"то\" \/>\n        <konst:int_const_elem cat=\"Part\" lu=\"чтобы\" name=\"чтобы\"\n        role=\"чтобы\" \/>\n        <konst:int_const_elem cat=\"AP\" msd=\"AdverbType=Comp\"\n        name=\"XP\" role=\"Property\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Gen\.Pl\"\n        name=\"NP-Gen\.Plur\" role=\"Set\" \/>\n        <konst:int_const_elem lu=\"но\" name=\"но\" role=\"но\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Part" lu="не" name="не" role="не" /><konst:int_const_elem lu="то" name="то" role="то" /><konst:int_const_elem cat="Part" lu="чтобы" name="чтобы" role="чтобы" /><konst:int_const_elem cat="AP" msd="AdverbType=Comp" name="Adv-Cmp" role="Property" /><konst:int_const_elem cat="AP" msd="AType=Comp" name="Adj-Cmp" role="Evaluation" /><konst:int_const_elem cat="NP" msd="NounType=Gen.Pl" name="NP-Gen.Plur" role="Set" /><konst:int_const_elem lu="но" name="но" role="но" /></Sense>', text)
    text = text.replace('<karp:text n="4">, убежал, словно заяц. Вот если б я его', '<karp:text n="4">Убежал, словно заяц. Вот если б я его')
    text = text.replace('<karp:e n="1" name="Action">имеющимся / только что', '<karp:e n="1" name="Action">имеющимся/только что')
    text = text.replace('konstruktikon-rus--NP-Nom_VP_по_NP-Dat', 'konstruktikon-rus--NP-Nom_VP_по_NP-Dat.Plur')
    text = text.replace('"[root [nsubj NP-Nom] VP [obl [case по] [NP-Dat]]"', '"[root [nsubj NP-Nom] VP [obl [case по] NP-Dat]]"')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"по\" name=\"по\" role=\"по\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Acc\"\n        name=\"Num-Acc\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Gen\"\n        name=\"NP-Gen\" role=\"Theme\" \/>\n        <konst:int_const_elem lu=\"за\" name=\"за\" role=\"за\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="по" name="по" role="по" /><konst:int_const_elem cat="NP" msd="NounType=Acc" name="Num-Acc" role="Number" /><konst:int_const_elem cat="NP" msd="NounType=Gen" name="NP-Gen" role="Theme" /><konst:int_const_elem lu="за" name="за" role="за" /><konst:int_const_elem cat="NP" msd="NounType=Acc" name="NP-Acc" role="Theme" /></Sense>', text)
    text = text.replace('[root [obl [case в] Сочи]] [obj мимозу] продают [obl [case по] [nummod два] рубля] [obl [case за] [nummod один] килограмм]]', '[root [obl [case в] Сочи] [obj мимозу] продают [obl [case по] [nummod два] рубля] [obl [case за] [nummod один] килограмм]]')
    text = text.replace('"[advcl Cl], [mark если] можно]"', '"[root [advcl Cl], [mark если] можно]"')
    text = text.replace('"[nsubj кофе], [mark если] можно]"', '"[root [nsubj кофе], [mark если] можно]"')
    text = text.replace('<konst:int_const_elem cat="VP" name="Action"', '<konst:int_const_elem cat="VP" name="VP"')
    text = text.replace('konstruktikon-rus--NP-Nom_VP_точно_так_же,_как_(и)_NP-Nom', 'konstruktikon-rus--NP-Nom1_VP_точно_так_же,_как_(и)_NP-Nom2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"точно\" name=\"точно\"\n        role=\"точно\" \/>\n        <konst:int_const_elem lu=\"так\" name=\"так\" role=\"так\" \/>\n        <konst:int_const_elem lu=\"же\" name=\"же\" role=\"же\" \/>\n        <konst:int_const_elem lu=\"как\" name=\"как\" role=\"как\" \/>\n        <konst:int_const_elem lu=\"и\" name=\"и\" role=\"и\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Standard\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"Participant\" role=\"Participant\" \/>\n        <konst:int_const_elem cat=\"VP\" name=\"VP\"\n        role=\"Action\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem lu="точно" name="точно" role="точно" /><konst:int_const_elem lu="так" name="так" role="так" /><konst:int_const_elem lu="же" name="же" role="же" /><konst:int_const_elem lu="как" name="как" role="как" /><konst:int_const_elem lu="и" name="и" role="и" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Standard" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Participant" /><konst:int_const_elem cat="VP" name="VP" role="Action" /></Sense>', text)
    text = re.sub('<konst:int_const_elem lu=\"закататиться\"\n        msd=\"VerbType=Perfective\" name=\"закататиться\" \/>', '<konst:int_const_elem lu="закатиться" msd="VerbType=Perfective" name="закатиться" />', text)
    text = text.replace('<konst:int_const_elem cat="VP" msd="VerbForm=Inf" name="VP"', '<konst:int_const_elem cat="VP" msd="VerbForm=Inf" name="VP-Inf"')
    text = text.replace('konstruktikon-rus--NP-Acc_прочить_NP-Ins|в_NP-Acc', 'konstruktikon-rus--NP-Acc1_прочить_NP-Ins|в_NP-Acc2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Experiencer\" \/>\n        <konst:int_const_elem lu=\"прочить\"\n        msd=\"VerbType=Imperfective\" name=\"прочить\"\n        role=\"прочить\" \/>\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Ins\"\n        name=\"NP-Ins\" role=\"Location\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Acc\"\n        name=\"NP-Acc\" role=\"Location\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Acc" name="NP-Acc1" role="Experiencer" /><konst:int_const_elem lu="прочить" msd="VerbType=Imperfective" name="прочить" role="прочить" /><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem cat="NP" msd="NounType=Ins" name="NP-Ins" role="Location" /><konst:int_const_elem cat="NP" msd="NounType=Acc" name="NP-Acc2" role="Location" /></Sense>', text)
    text = text.replace('[root [obj NP-Acc] прочить [obl NP-Ins]] | [obl [case в NP-Acc]]', '[root [obj NP-Acc] прочить [obl NP-Ins] | [obl [case в NP-Acc]]]')
    text = re.sub('<karp:e n=\"4\" name=\"Action\">\n              <karp:text n=\"0\">подавай<\/karp:text>\n              <karp:e n=\"1\" name=\"Participant\">ей<\/karp:e>\n              <karp:text n=\"2\">новое<\/karp:text>\n            <\/karp:e>', '<karp:text n="0">подавай</karp:text><karp:e n="1" name="Participant">ей</karp:e><karp:text n="2">новое</karp:text>', text)
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"VP\" lu=\"быть\" msd=\"VerbType=Fut\"\n        name=\"быть\" role=\"быть\" \/>\n        <konst:int_const_elem cat=\"VP\" lu=\"знать\" name=\"знать\"\n        role=\"знать\" \/>\n        <konst:int_const_elem lu=\"как\" name=\"как\" role=\"как\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="VP" lu="быть" msd="VerbType=Fut" name="быть-Fut" role="быть" /><konst:int_const_elem cat="VP" lu="знать" name="знать" role="знать" /><konst:int_const_elem lu="как" name="как" role="как" /><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /></Sense>', text)
    text = text.replace('konstruktikon-rus--быть-Fut_знать_как_Cl', 'konstruktikon-rus--быть-Fut_знать,_как_Cl')
    text = text.replace('konstruktikon-rus--NP-Nom,_конечно,_NP-Nom,_что_Cl', 'konstruktikon-rus--NP-Nom1,_конечно,_NP-Nom2,_что_Cl')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Agent\" \/>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"NP-Nom\" role=\"Assessment\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Action\" \/>\n        <konst:int_const_elem lu=\"конечно\" name=\"конечно\"\n        role=\"конечно\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom1" role="Agent" /><konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom2" role="Assessment" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem cat="Cl" name="Cl" role="Action" /><konst:int_const_elem lu="конечно" name="конечно" role="конечно" /></Sense>', text)
    text = re.sub('<karp:example>\n          <karp:text n=\"0\">умница</karp:text>\n        </karp:example>', '', text)
    text = text.replace('msd="AdjType=Nom|Ins" name="Adj" role="какой" />', 'msd="AdjType=Nom|Ins" name="какой" role="какой" />')
    text = text.replace('[root [nsubj [nmod [case из-за] ветра] скорость]] [cop была] [advmod не] ахти.]', '[root [nsubj [nmod [case из-за] ветра] скорость] [cop была] [advmod не] ахти.]')
    text = text.replace('<konst:int_const_elem lu="знать" name="знать" role="знает" />', '<konst:int_const_elem lu="знать" name="знает" role="знает" />')
    text = text.replace('<konst:int_const_elem lu="чёрт" name="чёрт" role="знает" />', '<konst:int_const_elem lu="чёрт" name="чёрт" role="чёрт" />')
    text = text.replace('konstruktikon-rus--Cl_до_той_поры,_пока/когда_Cl', 'konstruktikon-rus--Cl1_до_той_поры,_пока/когда_Cl2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Time\" \/>\n        <konst:int_const_elem lu=\"до\" name=\"до\" role=\"до\" \/>\n        <konst:int_const_elem lu=\"та\" name=\"той\" role=\"той\" \/>\n        <konst:int_const_elem lu=\"пора\" name=\"поры\" role=\"поры\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Cl" name="Cl1" role="Situation" /><konst:int_const_elem cat="Cl" name="Cl2" role="Time" /><konst:int_const_elem lu="до" name="до" role="до" /><konst:int_const_elem lu="та" name="той" role="той" /><konst:int_const_elem lu="пора" name="поры" role="поры" /><konst:int_const_elem lu="пока" name="пока" role="пока" /><konst:int_const_elem lu="когда" name="когда" role="когда" /></Sense>', text)
    text = text.replace('[root [nsubj он] не уйдет [obl [case до] [amod той] поры, [xcomp [advmod [advmod пока] [obl всё] не съест ]]]]', '[root [nsubj он] не уйдет [obl [case до] [amod той] поры, [xcomp [advmod [advmod пока] [obl всё] не съест]]]]')
    text = re.sub('<karp:e n=\"0\" name=\"Situation\">\n              <karp:text n=\"0\">Она готова работать у нас\n              бесплатно<\/karp:text>\n              <karp:e n=\"1\" name=\"до\">до<\/karp:e>\n              <karp:text n=\"2\" \/>\n              <karp:e n=\"3\" name=\"той\">той<\/karp:e>\n              <karp:text n=\"4\" \/>\n              <karp:e n=\"5\" name=\"поры\">поры<\/karp:e>\n              <karp:text n=\"6\" \/>\n            <\/karp:e>\n            <karp:text n=\"1\">,<\/karp:text>\n            <karp:e n=\"2\" name=\"Time\">\n              <karp:e n=\"0\" name=\"когда\">пока<\/karp:e>\n              <karp:text n=\"1\">появятся деньги<\/karp:text>\n            <\/karp:e>', '<karp:e n="0" name="Situation">Она готова работать у нас бесплатно</karp:e><karp:e n="1" name="до">до</karp:e><karp:text n="2" /><karp:e n="3" name="той">той</karp:e><karp:text n="4" /><karp:e n="5" name="поры">поры</karp:e><karp:text n="6" /><karp:text n="1">,</karp:text><karp:e n="0" name="когда">пока</karp:e><karp:text n="1">не появятся деньги</karp:text>', text)
    text = re.sub('<karp:e n=\"0\" name=\"Situation\">\n              <karp:text n=\"0\">Я сострадаю ровно<\/karp:text>\n              <karp:e n=\"1\" name=\"до\">до<\/karp:e>\n              <karp:text n=\"2\" \/>\n              <karp:e n=\"3\" name=\"той\">той<\/karp:e>\n              <karp:text n=\"4\" \/>\n              <karp:e n=\"5\" name=\"поры\">поры<\/karp:e>\n            <\/karp:e>\n            <karp:text n=\"1\">,<\/karp:text>\n            <karp:e n=\"2\" name=\"Time\">\n              <karp:text n=\"0\" \/>\n              <karp:e n=\"1\" name=\"пока\">пока<\/karp:e>\n              <karp:text n=\"2\">это не приносит мне\n              неудобств<\/karp:text>\n            <\/karp:e>', '<karp:e n="0" name="Situation">Я сострадаю ровно</karp:e><karp:e n="1" name="до">до</karp:e><karp:text n="2" /><karp:e n="3" name="той">той</karp:e><karp:text n="4" /><karp:e n="5" name="поры">поры</karp:e><karp:text n="1">,</karp:text><karp:text n="0" /><karp:e n="1" name="пока">пока</karp:e><karp:text n="2">это не приносит мне неудобств</karp:text>', text)
    text = re.sub('<karp:e n=\"0\" name=\"Situation,\">\n              <karp:text n=\"0\">дожив<\/karp:text>\n              <karp:e n=\"1\" name=\"до\">до<\/karp:e>\n              <karp:text n=\"2\" \/>\n              <karp:e n=\"3\" name=\"той\">той<\/karp:e>\n              <karp:text n=\"4\" \/>\n              <karp:e n=\"5\" name=\"поры\">поры<\/karp:e>\n              <karp:text n=\"6\" \/>\n            <\/karp:e>\n            <karp:text n=\"1\" \/>\n            <karp:e n=\"2\" name=\"Time\">\n              <karp:e n=\"0\" name=\"когда\">когда<\/karp:e>\n              <karp:text n=\"1\">люди научатся говорить\n              правду<\/karp:text>\n            <\/karp:e>', '<karp:e n="0" name="Situation,">дожив</karp:e><karp:e n="1" name="до">до</karp:e><karp:text n="2" /><karp:e n="3" name="той">той</karp:e><karp:text n="4" /><karp:e n="5" name="поры,">поры</karp:e><karp:text n="6" /><karp:text n="1" /><karp:e n="0" name="когда">когда</karp:e><karp:text n="1">люди научатся говорить правду</karp:text>', text)
    text = text.replace('konstruktikon-rus--легко_сказать_VP-Imper', 'konstruktikon-rus--легко_сказать,_VP-Imper')
    text = text.replace('[root [advmod то-то] [nsubj я] хочу [xcomp есть] !', '[root [advmod то-то] [nsubj я] хочу [xcomp есть!]]')
    text = text.replace('<konst:int_const_elem cat="Cl" name="Situation"', '<konst:int_const_elem cat="Cl" name="Cl"')
    text = text.replace('мог_бы_и_написать', 'мог бы и написать')
    text = text.replace('konstruktikon-rus--ни_слова_NP-Dat_о_NP-Dat!', 'konstruktikon-rus--ни_слова_NP-Dat1_о_NP-Dat2!')
    text = re.sub('<\/definition>\n        <konst:ext_const_elem lu=\"ни\" name=\"ни\" role=\"ни\" \/>\n        <konst:ext_const_elem lu=\"слово\" name=\"слова\"\n        role=\"слова\" \/>\n        <konst:ext_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"NP-Dat\" role=\"Experiencer\" \/>\n        <konst:ext_const_elem lu=\"о\" name=\"о\" role=\"о\" \/>\n        <konst:ext_const_elem cat=\"NP\" msd=\"NounType=Dat\"\n        name=\"NP-Dat\" role=\"Theme\" \/>\n      <\/Sense>', '</definition><konst:ext_const_elem lu="ни" name="ни" role="ни" /><konst:ext_const_elem lu="слово" name="слова" role="слова" /><konst:ext_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat1" role="Experiencer" /><konst:ext_const_elem lu="о" name="о" role="о" /><konst:ext_const_elem cat="NP" msd="NounType=Dat" name="NP-Dat2" role="Theme" /></Sense>', text)
    text = text.replace('[root [advmod ни] слова [nmod маме] [nmod [case о] [amod нашей] поездке]]', '[root [advmod ни] слова [nmod маме] [nmod [case о] [amod нашей] поездке!]]')
    text = text.replace('[root что [amod Adj-Gen]]?', '[root что [amod Adj-Gen?]]')
    text = text.replace('[root что [amod плохого]]?', '[root что [amod плохого?]]')
    text = text.replace('konstruktikon-rus--NP-Nom_VP-Inf(-то)_VP_но_Cl', 'konstruktikon-rus--NP-Nom_VP-Inf(-то)_VP,_но_Cl')
    text = text.replace('name="VP-Fut.P" role="Action" />', 'name="VP-Fut.Perf" role="Action" />')
    text = text.replace('konstruktikon-rus--подумаешь_(какой)_Cl', 'konstruktikon-rus--подумаешь,_(какой)_Cl')
    text = text.replace('[root подумаешь, [parataxis [amod какой] [ умник!]]', '[root подумаешь, [parataxis [amod какой] умник!]]')
    text = re.sub('<karp:e n=\"3\" name=\"Theme\">\n              <karp:text n=\"0\">воображала какая!<\/karp:text>\n              <karp:g n=\"1\" \/>\n            <\/karp:e>', '<karp:e n="3" name="Theme">воображала какая!</karp:e><karp:g n="1" />', text)
    text = re.sub('<konst:int_const_elem cat=\"Action\" name=\"Cl\"\n        role=\"VP\" />', '<konst:int_const_elem cat="Action" name="VP" role="VP" />', text)
    text = text.replace('[root VP [nsubj NP-Nom] [advmod наконец] [conj [cc или] нет]]?', '[root VP [nsubj NP-Nom] [advmod наконец] [conj [cc или] нет?]]')
    text = text.replace('<konst:int_const_elem aux="negative" cat="Adv" name="Adv"', '<konst:int_const_elem aux="negative" cat="Adv" name="не-Adv"')
    text = text.replace('<karp:e n="9" name="Event">некоторое событие.</karp:e>', '<karp:e n="9" name="Event">некоторое событие</karp:e>')
    text = text.replace('konstruktikon-rus--Num-Ins_Num-Nom_―_Num-Nom', 'konstruktikon-rus--Num-Ins_Num-Nom1_―_Num-Nom2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Instr\"\n        name=\"Num-Ins\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Nom\"\n        name=\"Num-Nom\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Nom\"\n        name=\"Num-Nom\" role=\"Result\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Num" msd="NumType=Instr" name="Num-Ins" role="Factor" /><konst:int_const_elem cat="Num" msd="NumType=Nom" name="Num-Nom1" role="Number" /><konst:int_const_elem cat="Num" msd="NumType=Nom" name="Num-Nom2" role="Result" /></Sense>', text)
    text = re.sub('<karp:e n=\"3\" name=\"Num-Ins\+Num-Nom\+―\+Num-Nom!\">\n            <karp:e n=\"0\" name=\"Factor\">Семью<\/karp:e>\n            <karp:text n=\"1\" \/>\n            <karp:e n=\"2\" name=\"Number\">семь<\/karp:e>\n            <karp:text n=\"3\">―<\/karp:text>\n            <karp:e n=\"4\" name=\"Result\">сорок девять<\/karp:e>\n            <karp:text n=\"5\" \/>\n          <\/karp:e>', '<karp:e n="0" name="Factor">Семью</karp:e><karp:text n="1" /><karp:e n="2" name="Number">семь</karp:e><karp:text n="3">―</karp:text><karp:e n="4" name="Result">сорок девять</karp:e><karp:text n="5" />', text)
    text = text.replace('[root [amod какой], [advmod к чёрту], сон]!', '[root [amod какой], [advmod к чёрту], сон!]')
    text = text.replace('konstruktikon-rus--Cl_без_того,_чтобы_Cl', 'konstruktikon-rus--Cl1_без_того,_чтобы_Cl2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Time\" \/>\n        <konst:int_const_elem lu=\"без\" name=\"без\" role=\"без\" \/>\n        <konst:int_const_elem lu=\"тот\" name=\"того\" role=\"того\" \/>\n        <konst:int_const_elem lu=\"чтобы\" name=\"чтобы\"\n        role=\"чтобы\" \/>\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Action\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Cl" name="Cl1" role="Time" /><konst:int_const_elem lu="без" name="без" role="без" /><konst:int_const_elem lu="тот" name="того" role="того" /><konst:int_const_elem lu="чтобы" name="чтобы" role="чтобы" /><konst:int_const_elem cat="Cl" name="Cl2" role="Action" /></Sense>', text)
    text = text.replace('konstruktikon-rus--Num-Nom_на_Num-Acc_―_Num-Nom', 'konstruktikon-rus--Num-Nom1_на_Num-Acc_―_Num-Nom2')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Nom\"\n        name=\"Num-Nom\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"PP\" lu=\"на\" name=\"на\"\n        role=\"на\" \/>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Acc\"\n        name=\"Num-Acc\" role=\"Number\" \/>\n        <konst:int_const_elem cat=\"Num\" msd=\"NumType=Nom\"\n        name=\"Num-Nom\" role=\"Result\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="Num" msd="NumType=Nom" name="Num-Nom1" role="Number" /><konst:int_const_elem cat="PP" lu="на" name="на" role="на" /><konst:int_const_elem cat="Num" msd="NumType=Acc" name="Num-Acc" role="Number" /><konst:int_const_elem cat="Num" msd="NumType=Nom" name="Num-Nom2" role="Result" /></Sense>', text)
    text = text.replace('konstruktikon-rus--Cl_скажи_нет', 'konstruktikon-rus--Cl,_скажи_нет')
    text = text.replace('[root cl [conj скажи [fixed нет]]]', '[root cl, [conj скажи [fixed нет]]]')
    text = text.replace('[root [obj [fixed мало ([advmod ли]]) SCONJ] Cl]', '[root [obj [fixed мало [(advmod ли)]] SCONJ] Cl]')
    text = text.replace('<konst:int_const_elem cat="DiscC" name="DiscC"', '<konst:int_const_elem cat="DiscCl" name="DiscCl"')
    text = text.replace('konstruktikon-rus--DiscCl_так,_Cl', 'konstruktikon-rus--DiscCl,_так,_Cl')
    text = text.replace('[root [nsubj она] [obl мне] [advmod не] нравилась], [conj [cc а] [parataxis так], баловство [amod одно]]]', '[root [nsubj она] [obl мне] [advmod не] нравилась, [conj [cc а] [parataxis так], баловство [amod одно]]]')
    text = re.sub('<karp:text n=\"1\">\"<\/karp:text>\n            <karp:g n=\"2\" \/>\n            <karp:text n=\"3\" \/>\n            <karp:e n=\"4\" name=\"так\">Так<\/karp:e>', '<karp:g n="2" /><karp:text n="3" /><karp:e n="4" name="так">"Так</karp:e>', text)
    text = re.sub('<karp:text n=\"1\">\"</karp:text>\n            <karp:e n=\"2\" name=\"так\">Так</karp:e>', '<karp:text n="1"></karp:text><karp:e n="2" name="так">"Так</karp:e>', text)
    text = text.replace('konstruktikon-rus--в_том-то_и_NP-Nom_Cl', 'konstruktikon-rus--в_том-то_и_NP-Nom,_Cl')
    text = re.sub('<\/definition>\n        <konst:int_const_elem lu=\"только\" name=\"только\"\n        role=\"только\" \/>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" \/>\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" \/>\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"State\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="NP" name="NP" role="Theme" /><konst:int_const_elem lu="только" name="только" role="только" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem lu="не" name="не" role="не" /><konst:int_const_elem cat="Clause" name="Cl" role="State" /></Sense>', text)
    text = re.sub('<karp:text n=\"0\">Люди \[беспокоятся\]Theme о бездомных\n          \[и\]Conj в то же время]в_то_же_время \[сторонятся\]Theme\n          их\.<\/karp:text>', '<karp:text n="0">Люди [беспокоятся]_Theme о бездомных [и]_Conj [в_то_же_время]_в+то+же+время [сторонятся]_Theme их.</karp:text>', text)
    text = text.replace('<karp:e n="1" name="Theme">факт</karp:e>', '<karp:e n="1" name="Theme,">факт</karp:e>')
    text = re.sub('<\/definition>\n        <konst:int_const_elem cat=\"PART\" lu=\"нет-нет\"\n        name=\"нет-нет\" role=\"нет-нет\" \/>\n        <konst:int_const_elem aux=\"facultative\" cat=\"CONJ\" lu=\"да\"\n        name=\"да\" role=\"да\" \/>\n        <konst:int_const_elem aux=\"facultative\" cat=\"CONJ\" lu=\"и\"\n        name=\"и\" role=\"и\" \/>\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" \/>\n      <\/Sense>', '</definition><konst:int_const_elem cat="PART" lu="нет-нет" name="нет-нет" role="нет-нет" /><konst:int_const_elem aux="facultative" cat="CONJ" lu="да" name="да" role="да" /><konst:int_const_elem aux="facultative" cat="CONJ" lu="и" name="и" role="и" /><konst:int_const_elem cat="VP" name="VP-Perf" role="Action" /></Sense>', text)
    text = text.replace('<karp:text n="3">; происходящего иногда, время от', '<karp:text n="3">, происходящего иногда, время от')
    text = text.replace('<karp:text n="2">, я вам</karp:text>', '<karp:text n="2">я вам</karp:text>')
    text = re.sub('<konst:int_const_elem cat=\"NP\" msd=\"NounType=Nom\"\n        name=\"Agent\" role=\"Agent\" />', '<konst:int_const_elem cat="NP" msd="NounType=Nom" name="NP-Nom" role="Agent" />', text)
    text = text.replace('konstruktikon-rus--NP-Dat_VP-Inf_быть_в_лом', 'konstruktikon-rus--NP-Dat_VP-Inf_быть_влом')
    text = re.sub('<konst:int_const_elem cat=\"Preposition\" lu=\"в\" name=\"в\"\n        role=\"в\" \/>\n        <konst:int_const_elem lu=\"лом\" name=\"лом\" role=\"лом\" \/>', '<konst:int_const_elem cat="Adverb" lu="влом" name="влом" role="влом" />', text)
    text = text.replace('[root [obl Маше] вставать [obj [case с] кровати] [aux было] [advmod [fixed в] лом]]', '[root [obl Маше] вставать [obj [case с] кровати] [aux было] [advmod влом]]')
    text = text.replace('Маше вставать с кровати было в лом', 'Маше вставать с кровати было влом')
    text = text.replace('[root [obl NP-Dat] VP-Inf [aux быть] [advmod [fixed в] лом]]', '[root [obl NP-Dat] VP-Inf [aux быть] [advmod влом]]')
    text = re.sub('<feat att=\"cee\" val=\"в\" \/>\n        <feat att=\"cee\" val=\"лом\" \/>', '<feat att="cee" val="влом" />', text)
    text = re.sub('<karp:e n=\"6\" name=\"в\">в</karp:e>\n            <karp:text n=\"7\" />\n            <karp:e n=\"8\" name=\"лом\">лом</karp:e>', '<karp:e n="6" name="влом">влом</karp:e>', text)
    text = re.sub('<karp:e n=\"4\" name=\"в\">в</karp:e>\n            <karp:text n=\"5\" />\n            <karp:e n=\"6\" name=\"лом\">лом</karp:e>', '<karp:e n="4" name="влом">влом</karp:e>', text)
    text = re.sub('<karp:e n=\"2\" name=\"в\">в</karp:e>\n            <karp:text n=\"3\" />\n            <karp:e n=\"4\" name=\"лом\">лом</karp:e>', '<karp:e n="2" name="влом">влом</karp:e>', text)
    text = text.replace('konstruktikon-rus--чем_бы_VP_VP_(бы)', 'konstruktikon-rus--чем_бы_VP,_VP_(бы)')
    text = text.replace('<konst:ext_const_elem cat="NP" name="Participant"', '<konst:ext_const_elem cat="NP" name="NP-Nom"')
    text = text.replace('Жена его все-равно', 'Жена его все равно')
    text = text.replace('konstruktikon-rus--VP-Imper_ещё_(мне/(у)_меня)', 'konstruktikon-rus--VP-Imper_ещё_(мне)/(у)_меня')
    text = text.replace('[root VP-Imper [advmod ещё] [obl мне]]/ [obl [case у] меня]]', '[root VP-Imper [advmod ещё] [obl мне] [obl [case у] меня]]')
    text = text.replace('konstruktikon-rus--ввиду_того,_что_Cl_Cl', 'konstruktikon-rus--ввиду_того,_что_Cl,_Cl')
    text = text.replace('[благоволите[VP-Inf]]', '[root [благоволите VP-Inf]]')
    text = text.replace('konstruktikon-rus--только_и_знать_что_Cl', 'konstruktikon-rus--только_и_знать,_что_Cl')
    text = text.replace('[только[и[знать[что[Cl]]]]]', '[root только и знать, что Cl]')
    text = text.replace('name="NP-Instr" role="Standard" />', 'name="NP-Ins" role="Standard" />')
    text = text.replace('konstruktikon-rus--Cl_(да)_что_(тут)_говорить!', 'konstruktikon-rus--Cl_(да)_что_(тут/и)_говорить!')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" />\n        <konst:int_const_elem lu=\"говорить\" name=\"говорить\"\n        role=\"говорить\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"и\" name=\"и\" role=\"и\" />\n        <konst:int_const_elem lu=\"да\" name=\"да\" role=\"да\" />\n      </Sense>', '</definition><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem lu="говорить" name="говорить" role="говорить" /><konst:int_const_elem cat="Cl" name="Cl" role="Theme" /><konst:int_const_elem lu="и" name="и" role="и" /><konst:int_const_elem lu="да" name="да" role="да" /><konst:int_const_elem lu="тут" name="тут" role="тут" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP-Nom_только_и_делать,_что_Cl', 'konstruktikon-rus--NP-Nom_только_и_делать,_что_VP')
    text = text.replace('[root [advmod только] [advmod и] разговоров], [mark что] [advcl [case о] доме]]', '[root [advmod только] [advmod и] разговоров, [mark что] [advcl [case о] доме]]')
    text = text.replace('<konst:ext_const_elem cat="VP" name="Action"', '<konst:ext_const_elem cat="VP" name="VP"')
    text = text.replace('<konst:ext_const_elem cat="NP" name="Agent" role="Agent" />', '<konst:ext_const_elem cat="NP" name="NP" role="Agent" />')
    text = text.replace('<konst:int_const_elem cat="NP" name="Agent" role="Agent" />', '<konst:int_const_elem cat="NP" name="NP" role="Agent" />')
    adj = ['Adj-Acc', 'Adj-Cmp', 'Adj-Gen', 'Adj-Ins', 'Adj-Nom', 'ADJ-Short', 'Adj-Short', 'Adj-ее', 'ADJ-Cmp', 'Adj-Сmp']
    for i in range(len(adj)):
        text = text.replace(adj[i], 'Adj')
    text = text.replace('Adv-Cmp', 'Adv')
    text = text.replace('AP-Nom', 'AP')
    text = text.replace('AP-Short', 'AP')
    text = text.replace('[root [nmod [case ввиду] того, [mark что] [advcl Cl]], Cl]', '[root [nmod [case ввиду] того, [mark что] [advcl Cl1]], Cl2]')
    text = text.replace('<konst:int_const_elem cat="Clause" name="Cause"', '<konst:int_const_elem cat="Clause" name="Cl"')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"ввиду\" name=\"ввиду\"\n        role=\"ввиду\" />\n        <konst:int_const_elem lu=\"то\" name=\"того\" role=\"того\" />\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" />\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Cause\" />\n        <konst:int_const_elem cat=\"Clause\" name=\"Cl\"\n        role=\"Circumstance\" />\n      </Sense>', '</definition><konst:int_const_elem lu="ввиду" name="ввиду" role="ввиду" /><konst:int_const_elem lu="то" name="того" role="того" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem cat="Clause" name="Cl1" role="Cause" /><konst:int_const_elem cat="Clause" name="Cl2" role="Circumstance" /></Sense>', text)
    text = text.replace('<konst:ext_const_elem name="Condition" role="Condition" />', '<konst:ext_const_elem name="Cl" role="Condition" />')
    text = text.replace('DiscCl', 'Cl')
    text = text.replace('konstruktikon-rus--Cl,_так,_Cl', 'konstruktikon-rus--Cl1,_так,_Cl2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"так\" name=\"так\" role=\"так\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Context\" />\n      </Sense>', '</definition><konst:int_const_elem lu="так" name="так" role="так" /><konst:int_const_elem cat="Cl" name="Cl1" role="Theme" /><konst:int_const_elem cat="Cl" name="Cl2" role="Context" /></Sense>', text)
    text = text.replace('Itg', 'Intj')
    noun = ['Noun-Dat.Plur', 'Noun-Ins', 'Noun-ище']
    for elem in noun:
        text = text.replace(elem, 'Noun')
    np_ = ['NP-Acc', 'NP-Dat.Plur', 'NP-Dat', 'NP-Gen.Plur', 'NP-Gen', 'NP-Ins.Plur', 'NP-Ins/Nom', 'NP-Ins', 'NP-Loc', 'NP-Nom.Plur', 'NP-Nom.Pl', 'NP-Nom', 'NP-Plur']
    for elem in np_:
        text = text.replace(elem, 'NP')
    num = ['NUM-Acc', 'NUM-Gen', 'NUM-Ins', 'NUM-Nom', 'Num-Acc', 'Num-Gen', 'Num-Ins', 'Num-Nom']
    for elem in num:
        text = text.replace(elem, 'Num')
    text = text.replace('<konst:int_const_elem cat="NP" name="Participant"', '<konst:int_const_elem cat="NP" name="NP"')
    text = text.replace('Pron-2.Dat', 'Pron-2')
    pron = ['PRON-Nom', 'Pron-Nom', 'Pron-Dat', 'Pron-Gen', 'Pron-Ins']
    for elem in pron:
        text = text.replace(elem, 'Pron')
    text = text.replace('<konst:ext_const_elem cat="Clause" name="Situation"', '<konst:ext_const_elem cat="Clause" name="Cl"')
    text = text.replace('<konst:ext_const_elem cat="Cl" name="Situation"', '<konst:ext_const_elem cat="Cl" name="Cl"')
    text = text.replace('<konst:ext_const_elem cat="NP" name="Stimulus"', '<konst:ext_const_elem cat="NP" name="NP"')
    text = text.replace('<konst:int_const_elem name="Theme" role="Theme" />', '<konst:int_const_elem name="XP" role="Theme" />')
    text = text.replace('<konst:ext_const_elem cat="NP" name="Theme" role="Theme" />', '<konst:ext_const_elem cat="NP" name="NP" role="Theme" />')
    text = text.replace('<konst:int_const_elem cat="Theme" name="Theme" role="Cl" />', '<konst:int_const_elem cat="Theme" name="Cl" role="Cl" />')    
    text = text.replace('V-Past', 'V')
    text = text.replace('V-Pres.2.Sing', 'V')
    vp = ['VP-Fut.1.Plur','VP-Fut.Perf','VP-Fut','VP-Imp.Inf','VP-Imper','VP-Imp','VP-Inf.Imp','VP-Inf.Perf','VP-Inf','VP-Past.Perf','VP-Past','VP-Perf.Fut','VP-Perf.Past','VP-Perf','VP-Pres.2.Sing']
    for elem in vp:
        text = text.replace(elem, 'VP')
    text = text.replace('VP-ся', 'VP')
    text = text.replace('в-VP', 'VP')
    text = text.replace('бросать-Imper', 'бросать')
    text = text.replace('быть-Fut', 'быть')
    text = text.replace('быть-Past', 'быть')
    text = text.replace('давать-Imper', 'давать')
    text = text.replace('до-VP', 'VP')
    text = text.replace('другой-Gen', 'другой')
    text = text.replace('единый-Gen', 'единый')
    text = text.replace('мочь-Past', 'мочь')
    text = text.replace('на-VP', 'VP')
    text = text.replace('над-VP', 'VP')
    text = text.replace('наи-Adj-ший', 'Adj')
    text = text.replace('наи-Аdj-ший', 'Adj')
    text = text.replace('найти-Past', 'найти')
    text = text.replace('не-Adv', 'Adv')
    text = text.replace('оставить-Imper', 'оставить')
    text = text.replace('пере-VP', 'VP')
    text = text.replace('по-VP', 'VP')
    text = text.replace('полный-Short', 'полный')
    text = text.replace('раз-Gen', 'раз')
    text = text.replace('прийтись-Past', 'прийтись')
    text = text.replace('принять-Past', 'принять')
    text = text.replace('созданный-Short', 'созданный')
    text = text.replace('умирать-Pres.1.Sing', 'умирать')
    text = text.replace('характер-Acc', 'характер')
    text = text.replace('хороший-Short', 'хороший')
    text = text.replace('этот-Nom', 'этот')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"вот\" name=\"вот\" role=\"вот\" />\n        <konst:int_const_elem lu=\"бы\" name=\"бы\" role=\"бы\" />\n        <konst:int_const_elem cat=\"Cl\"\n        msd=\"VerbType=Inf\|VP\.Imp-Pst\" name=\"Cl\" role=\"Situation\" />\n      </Sense>', '</definition><konst:int_const_elem lu="вот" name="вот" role="вот" /><konst:int_const_elem lu="бы" name="бы" role="бы" /><konst:int_const_elem cat="Cl" msd="VerbType=Inf" name="Cl1" role="Situation" /><konst:int_const_elem cat="Cl" msd="VerbType=VP.Imp-Pst" name="Cl2" role="Situation" /></Sense>', text)
    text = text.replace('"AdjectiveType=Cmp"', '"AdjType=Cmp"')
    text = text.replace('"AdjectiveType=Comp"', '"AdjType=Comp"')
    text = text.replace('"AdjectiveType=Comparative"', '"AdjType=Comparative"')
    text = text.replace('"AdjectiveType=Supr"', '"AdjType=Supr"')
    text = text.replace('"AdverbType=Comp"', '"AdvType=Comp"')
    text = text.replace('"Mood=Imperative"', '"Mood=Imper"')
    text = text.replace('"NP=Gen"', '"Case=Gen"')
    text = text.replace('"msd="NPt"', 'msd="NP"')
    text = text.replace('"NoinType=Nom"', '"Case=Nom"')
    text = text.replace('"NounCase=Gen"', '"Case=Gen"')
    text = text.replace('"NounType-Dat"', '"Case=Dat"')
    text = text.replace('"NounType=Inf"', '"VerbType=Inf"')
    rep = ['NounType=Acc', 'NounType=Dat', 'NounType=Gen', 'NounType=Gen2', 'NounType=Ins', 'NounType=Loc', 'NounType=Nom', 'Nountype=Dat']
    for elem in rep:
        text = text.replace('"' + elem + '"', '"' + 'Case=' + elem.split('=')[1] + '"')
    text = text.replace('"Case=Dat|Number=Plur"', '"Case=Dat|Number=Pl"')
    text = text.replace('"NounType=Dat.Plur"', '"Case=Dat|Number=Pl"')
    text = text.replace('"NounType=Dat.Sg"', '"Case=Dat|Number=Sg"')
    text = text.replace('"NounType=Gen|Acc"', '"Case=Gen|Case=Acc"')
    text = text.replace('"NounType=Gen, Plur"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NounType=Gen.Pl"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NounType=Gen.Plur"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NounType=Loc.Plur"', '"Case=Loc|Number=Pl"')
    text = text.replace('"NounType=Nom.Pl"', '"Case=Nom|Number=Pl"')
    text = text.replace('"NounType=Nom.Sing"', '"Case=Nom|Number=Sg"')
    text = text.replace('"NounType=Pl, Gen"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NounType=Plur"', '"Number=Pl"')
    text = text.replace('"NounType=Plur, Gen"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NountType=Genitive.Plur"', '"Case=Gen|Number=Pl"')
    text = text.replace('"NounType=Accusative"', '"Case=Acc"')
    text = text.replace('"NounType=Dative"', '"Case=Dat"')
    text = text.replace('"NounType=Inst"', '"Case=Ins"')
    text = text.replace('"NounType=Instr"', '"Case=Ins"')
    text = text.replace('"NounType=Instrum"', '"Case=Ins"')
    text = text.replace('"NounType=Instrumental"', '"Case=Ins"')
    rep = ['NumCase=Acc', 'NumType=Acc', 'NumType=Gen', 'NumType=Nom', 'NumberType=Dat', 'PRONType=Dat', 'PRONType=Gen', 'PRONType=Nom']
    for elem in rep:
        text = text.replace('"' + elem + '"', '"' + 'Case=' + elem.split('=')[1] + '"')
    text = text.replace('"NumType=Instr"', '"Case=Ins"')
    text = text.replace('"Number=Plur|Case=Gen"', '"Case=Gen|Number=Pl"')
    text = text.replace('"PronType=Dative"', '"Case=Dat"')
    text = text.replace('"PronType=2.Dat"', '"Case=Dat|Person=2p"')
    rep = ['PronType=Dat', 'PronType=Gen', 'PronType=Ins', 'PronType=Nom','Type=Acc','Type=Dat','Type=Gen','Type=Nom', 'AdjType=Gen','AdjType=Ins','AdjType=Nom', 'AdjType=Acc', 'NpType=Gen']
    for elem in rep:
        text = text.replace('"' + elem + '"', '"' + 'Case=' + elem.split('=')[1] + '"')
    text = text.replace('"AdjType=Comp"', '"AdjType=Cmp"')
    text = text.replace('"AdvType=Comp"', '"AdvType=Cmp"')
    text = text.replace('"AdjType=Comparative"', '"AdjType=Cmp"')
    text = text.replace('"AdjType=Сmp"', '"AdjType=Cmp"')
    text = text.replace('"AdjType=Nom|Ins"', '"Case=Nom|Case=Ins"')
    text = text.replace('"Tense=Past"', '"Tense=Pst"')
    text = text.replace('"Type=Past"', '"Tense=Pst"')
    text = text.replace('"Type=Plural"', '"Number=Pl"')
    text = text.replace('"Type=Perfective"', '"Aspect=Pf"')
    text = text.replace('"VerbType=2SG, FUT"', '"Tense=Fut|Person=2p|Number=Sg"')
    text = text.replace('"VerbType=Pres.2.Sing"', '"Tense=Prs|Person=2p|Number=Sg"')
    text = text.replace('"VerbType=Fut"', '"Tense=Fut"')
    text = text.replace('"VerbType=PRS"', '"Tense=Prs"')
    text = text.replace('"VerbType=PST"', '"Tense=Pst"')
    text = text.replace('"VerbType=Past"', '"Tense=Pst"')
    text = text.replace('"VerbType=Past/Pres"', '"Tense=Pst|Tense=Prs"')
    text = text.replace('"VerbType=Present|Fut"', '"Tense=Prs|Tense=Fut"')
    text = text.replace('"VerbType=Pst"', '"Tense=Pst"')
    text = text.replace('"Verbtype=Imperfect"', '"Aspect=Ipf"')
    text = text.replace(' msd="а" ', ' lu="а" ')
    text = text.replace(' msd="и" ', ' lu="и" ')
    text = text.replace(' msd="что" ', ' lu="что" ')
    text = text.replace(' msd="что-то" ', ' lu="что-то" ')
    text = text.replace(' msd="знать" ', ' lu="знать" ')
    text = text.replace('"VervType=Imperfective"', '"Aspect=Ipf"')
    text = text.replace('"VerbType=Imp"', '"Aspect=Ipf"')
    text = text.replace('"VetbType=Perfective"', '"Aspect=Pf"')
    text = text.replace('"VerbType=Perf"', '"Aspect=Pf"')
    text = text.replace('"VerbType=Perfect"', '"Aspect=Pf"')
    text = text.replace('"VerbType=Imper"', '"Mood=Imper"')
    text = text.replace('"VerbType=Imperativ"', '"Mood=Imper"')
    text = text.replace('"VerbType=Imperfective"', '"Aspect=Ipf"')
    text = text.replace('"VerbForm=Inf"', '"Mood=Inf"')
    text = text.replace('"VerbType-Inf"', '"Mood=Inf"')
    text = text.replace('"VerbType=Inf"', '"Mood=Inf"')
    text = text.replace('"VerbType=Infinitive"', '"Mood=Inf"')
    text = text.replace('"VerbType=infinitive"', '"Mood=Inf"')
    text = text.replace('"VerbType=Inf, Imp"', '"Mood=Inf|Aspect=Ipf"')
    text = text.replace('"VerbType=Inf, Ipfv"', '"Mood=Inf|Aspect=Ipf"')
    text = text.replace('"VerbType=Inf.Imp"', '"Mood=Inf|Aspect=Ipf"')
    text = text.replace('"VerbType=Inf.Perf"', '"Mood=Inf|Aspect=Pf"')
    text = text.replace('"VerbType=Inf.Perfect"', '"Mood=Inf|Aspect=Pf"')
    text = text.replace('"VP=Inf.Perfect"', '"Mood=Inf|Aspect=Pf"')
    text = text.replace('"VervType=Inf.Perf"', '"Mood=Inf|Aspect=Pf"')
    text = text.replace('"VerbType=Pst | Inf"', '"Mood=Inf|Tense=Pst"')
    text = text.replace('"AdverbType"', '"Adv"')
    text = text.replace('"AType=Comp"', '"Adj=Comp"')
    text = text.replace('msd="NPt"', 'msd="NP"')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"VP\" lu=\"быть\" name=\"будучи\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NP\" name=\"NP\"\n        role=\"Theme\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" />\n      </Sense>', '</definition><konst:int_const_elem cat="VP" lu="быть" name="будучи" /><konst:int_const_elem cat="NP" msd="Case=Ins" name="NP" role="Theme" /><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"VP\" msd=\"Mood=Inf\|Aspect=Pf\"\n        name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem cat=\"VP\" lu=\"велеть\" name=\"велеть\"\n        role=\"велеть\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType\" name=\"NP\"\n        role=\"Recipient\" />\n      </Sense>', '</definition><konst:int_const_elem cat="VP" msd="Mood=Inf|Aspect=Pf" name="VP" role="Action" /><konst:int_const_elem cat="VP" lu="велеть" name="велеть" role="велеть" /><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP" role="Recipient" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NP\" lu=\"условие\" name=\"условиях\"\n        role=\"условиях\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NP\" name=\"NP\"\n        role=\"Theme\" />\n        <konst:int_const_elem cat=\"Cl\" name=\"Cl\"\n        role=\"Situation\" />\n      </Sense>', '</definition><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem cat="NP" lu="условие" name="условиях" role="условиях" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP" role="Theme" /><konst:int_const_elem cat="Cl" name="Cl" role="Situation" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Goal\"\n        name=\"NP\" role=\"Goal\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem msd=\"Case=Acc\" name=\"честь\"\n        role=\"честь\" />\n        <konst:int_const_elem cat=\"Sl\" name=\"Cl\"\n        role=\"Situation\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP" role="Goal" /><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem msd="Case=Acc" name="честь" role="честь" /><konst:int_const_elem cat="Sl" name="Cl" role="Situation" /></Sense>' , text)
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Time\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=NP\"\n        name=\"Num\" role=\"Number\" />\n        <konst:int_const_elem lu=\"на\" name=\"на\" role=\"на\" />\n      </Sense>', '</definition><konst:int_const_elem cat="VP" name="VP" role="Action" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP" role="Time" /><konst:int_const_elem cat="NP" msd="Case=Acc" name="Num" role="Number" /><konst:int_const_elem lu="на" name="на" role="на" /></Sense>', text)
    text = text.replace('"NounType=Prep"', '"Case=Abl"')
    text = text.replace('<konst:int_const_elem cat="Num" msd="NumberType=Num"', '<konst:int_const_elem cat="Num" msd="Case=Gen"')
    text = text.replace('msd="Part"', 'msd="Part="')
    text = text.replace('msd="Particle"', 'msd="Part="')
    text = text.replace('msd="PartType=Neg"', 'msd="Part=Neg"')
    text = text.replace('msd="ParticleType=Negative"', 'msd="Part=Neg"')
    text = text.replace('msd="PartType=Negative"', 'msd="Part=Neg"')
    text = text.replace('msd="PartType=limiting"', 'msd="Part=Limiting"')
    text = text.replace('msd="ParticleType=limiting"', 'msd="Part=Limiting"')
    text = text.replace('msd="Past"', 'msd="Tense=Pst"')
    text = text.replace('msd="Pr"', 'msd="Prep="')
    text = text.replace('msd="Prep"', 'msd="Prep="')
    text = text.replace('msd="Preposition"', 'msd="Prep="')
    text = text.replace('PrepositionType=place', 'Prep=Place')
    text = text.replace('PronType=Interrog', 'Pron=Interrog')
    text = text.replace('msd="Pron"', 'msd="Pron="')
    text = text.replace('PronType=Neg', 'Pron=Neg')
    text = text.replace('Pron=Negative', 'Pron=Neg')
    text = text.replace('PronType=Personal', 'Pron=Personal')
    text = text.replace('"VerbType=VP.Imp-Pst"', '"Aspect=Ipf|Tense=Pst"')
    adjs = ['AdjType=Cmp','AdjType=Descr','AdjType=Plen','AdjType=Short','AdjType=Supr', 'AdvType=Cmp','AdvType=Degree']
    for adj in adjs:
        text = text.replace(adj, adj.replace('Type', ''))
    text = text.replace('msd="Adv"', 'msd="Adv="')
    text = text.replace('Verbtype=Inf', 'Mood=Inf')
    text = text.replace('VerbType=Trans', 'Trans=Tran')
    text = text.replace('msd="было"', 'msd="Tense=Pst|Person=3p|Gender=n"')
    text = text.replace('VerbType=Perfective', 'Aspect=Pf')
    refls = ['VebType=Reflexive', 'VerbType=Reflexive', 'Verbtype=Reflexive']
    for refl in refls:
        text = text.replace(refl, 'Verb=Reflexive')
    text = text.replace('msd="VerbType"', 'msd="Verb="')
    text = text.replace('VerbType=Action', 'Verb=')
    text = text.replace('VerbType=Short', 'Verb=Short')
    text = text.replace('VerbType=Praet', 'Tense=Pst|Person=3p|Gender=n')
    text = text.replace('"Aspect=Pf=Fut"', '"Aspect=Pf|Tense=Fut"')
    text = text.replace('Misc=Intrans', 'Trans=Intr')
    text = text.replace('"VerbType=Imp.Past"', '"Aspect=Ipf|Tense=Pst"')
    text = text.replace('"konstruktikon-rus--вот_бы_Cl"', '"konstruktikon-rus--вот_бы_Cl1/Cl2"')    
    text = text.replace('"VerbType=Past.Perf"', '"Aspect=Pf|Tense=Pst"')
    text = text.replace('"VerbType=Perf.Past"', '"Aspect=Pf|Tense=Pst"')
    text = text.replace('"Case=Gen2"', '"Case=Part"')
    text = text.replace('konstruktikon-rus--по_Num_(NP1)_NP2', 'konstruktikon-rus--по_Num_(NP1/NP2)_NP3')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\|Case=Acc\" name=\"NP1\" role=\"Container\" /><konst:int_const_elem cat=\"Num\" msd=\"Case=Dat\" name=\"Num\" role=\"Number\" /><konst:int_const_elem cat=\"Prep\" lu=\"по\" name=\"по\" role=\"по\" /><konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\" name=\"NP2\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP1" role="Container" /><konst:int_const_elem cat="NP" msd="Case=Acc" name="NP2" role="Container" /><konst:int_const_elem cat="Num" msd="Case=Dat" name="Num" role="Number" /><konst:int_const_elem cat="Prep" lu="по" name="по" role="по" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP3" role="Theme" /></Sense>', text)
    text = text.replace('name="AP"', 'name="Adj"')
    text = text.replace('_AP', '_Adj')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Protagonist\" />\n        <konst:int_const_elem cat=\"AdjP\" msd=\"Case=Nom\"\n        name=\"Adj\" role=\"Evaluation\" />\n        <konst:int_const_elem lu=\"до\" name=\"до\" role=\"до\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Protagonist" /><konst:int_const_elem cat="AdjP" msd="Case=Nom" name="Adj" role="Evaluation" /><konst:int_const_elem lu="до" name="до" role="до" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('Adj=Short', 'Adj=Brev')
    text = text.replace('Adj=Cmp', 'Adj=Comp')
    text = text.replace('Adv=Cmp', 'Adv=Comp')
    text = text.replace('Adj=Descr', 'Adj=Plen')    
    text = text.replace('msd="Adj=Comp" name="Adv"', 'msd="Adj=Comp" name="Adj"')
    text = text.replace('_Pron-2', '_Pron')
    text = text.replace('name="Pron-2"', 'name="Pron"')
    text = text.replace('"konstruktikon-rus--NP_чуть_не_VP"', '"konstruktikon-rus--NP_чуть_не_VP1/VP2"')
    text = text.replace('<konst:int_const_elem cat="VP" msd="Tense=Pst|Tense=Prs" name="VP" role="Action" />', '<konst:int_const_elem cat="VP" msd="Tense=Pst" name="VP1" role="Action" /><konst:int_const_elem cat="VP" msd="Tense=Prs" name="VP2" role="Action" />')
    text = text.replace('"Mood=Ind|Tense=Pst"', '"Mood=Indic|Tense=Pst"')
    text = text.replace('Tense=Pst', 'Tense=Praet')
    text = text.replace('Tense=Fut', 'Tense=Inpraes')
    text = text.replace('Tense=Prs', 'Tense=Praes')
    text = text.replace('konstruktikon-rus--XP_так_XP', 'konstruktikon-rus--XP1_так_XP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Part\" lu=\"так\"\n        msd=\"Part=Limiting\" name=\"так\" />\n        <konst:int_const_elem cat=\"XP\" msd=\"Case=Nom\" name=\"XP\"\n        role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Part" lu="так" msd="Part=Limiting" name="так" /><konst:int_const_elem cat="XP" msd="Case=Nom" name="XP1" role="Theme" /><konst:int_const_elem cat="XP" msd="Case=Nom" name="XP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--сегодня_XP,_завтра_XP', 'konstruktikon-rus--сегодня_XP1,_завтра_XP2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"сегодня\" name=\"сегодня\"\n        role=\"сегодня\" />\n        <konst:int_const_elem lu=\"завтра\" name=\"завтра\"\n        role=\"завтра\" />\n        <konst:int_const_elem name=\"XP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem lu="сегодня" name="сегодня" role="сегодня" /><konst:int_const_elem lu="завтра" name="завтра" role="завтра" /><konst:int_const_elem name="XP1" role="Theme" /><konst:int_const_elem name="XP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_прямо_VP/NP', 'konstruktikon-rus--NP1_прямо_VP/NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Agent\" />\n        <konst:int_const_elem lu=\"прямо\" name=\"прямо\"\n        role=\"прямо\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Agent" /><konst:int_const_elem lu="прямо" name="прямо" role="прямо" /><konst:int_const_elem cat="VP" name="VP" role="Action" /><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_(быть)_как_NP', 'konstruktikon-rus--NP1_(быть)_как_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Standard\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"как\" name=\"как\" />\n        <konst:int_const_elem lu=\"быть\" name=\"быть\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Standard" /><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP2" role="Theme" /><konst:int_const_elem lu="как" name="как" /><konst:int_const_elem lu="быть" name="быть" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_в_NP', 'konstruktikon-rus--NP1_в_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Property\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" name="NP1" role="Theme" /><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem cat="NP2" msd="Case=Acc" name="NP2" role="Property" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_звать_NP', 'konstruktikon-rus--NP1_звать_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Participant\" />\n        <konst:int_const_elem cat=\"VP\" lu=\"звать\"\n        msd=\"Mood=Inf\" name=\"звать\" />\n        <konst:int_const_elem aux=\"NounType=Nominative\" cat=\"NP\"\n        msd=\"Case=Ins\" name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Acc" name="NP1" role="Participant" /><konst:int_const_elem cat="VP" lu="звать" msd="Mood=Inf" name="звать" /><konst:int_const_elem aux="NounType=Nominative" cat="NP" msd="Case=Ins" name="NP2" role="Theme" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"а\" name=\"а\" role=\"а\" />\n        <konst:int_const_elem lu=\"что\" name=\"что\" role=\"что\" />\n        <konst:int_const_elem lu=\"насчёт\" name=\"насчёт\"\n        role=\"насчёт\" />\n        <konst:int_const_elem cat=\"XP\" name=\"XP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem lu="а" name="а" role="а" /><konst:int_const_elem lu="так" name="так" role="так" /><konst:int_const_elem lu="что" name="что" role="что" /><konst:int_const_elem lu="насчёт" name="насчёт" role="насчёт" /><konst:int_const_elem cat="XP" name="XP" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_из_NP', 'konstruktikon-rus--NP1_из_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\" name=\"NP\"\n        role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\|Number=Pl\"\n        name=\"NP\" role=\"Set\" />\n        <konst:int_const_elem lu=\"из\" name=\"из\" role=\"из\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem cat="NP" msd="Case=Gen|Number=Pl" name="NP2" role="Set" /><konst:int_const_elem lu="из" name="из" role="из" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"из-за\" name=\"из-за\"\n        role=\"из-за\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Reason\" />\n        <konst:ext_const_elem cat=\"Cl\" name=\"Cl\" role=\"Event\" />\n      </Sense>', '</definition><konst:int_const_elem lu="из-за" name="из-за" role="из-за" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP" role="Reason" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_закатиться|залиться_NP', 'konstruktikon-rus--NP1_закатиться|залиться_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem aux=\"animate\" cat=\"NP\"\n        msd=\"Case=Nom\" name=\"NP\" role=\"Experiencer\" />\n        <konst:int_const_elem lu=\"закатиться\" msd=\"Aspect=Pf\" name=\"закатиться\" />\n        <konst:int_const_elem lu=\"залиться\"\n        msd=\"Aspect=Pf\" name=\"залиться\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem aux="animate" cat="NP" msd="Case=Nom" name="NP1" role="Experiencer" /><konst:int_const_elem lu="закатиться" msd="Aspect=Pf" name="закатиться" /><konst:int_const_elem lu="залиться" msd="Aspect=Pf" name="залиться" /><konst:int_const_elem cat="NP" msd="Case=Ins" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('<konst:int_const_elem lu="закатиться" msd="Aspect=Pf" name="закатиться" />', '<konst:int_const_elem lu="закатываться" msd="Aspect=Pf" name="закатиться" />')
    text = text.replace('<feat att="cee" val="закатиться" />', '<feat att="cee" val="закатиться" /><feat att="cee" val="закатываться" />')
    text = text.replace('konstruktikon-rus--NP_есть_NP', 'konstruktikon-rus--NP1_есть_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"VP\" lu=\"быть\" name=\"есть\"\n        role=\"есть\" />\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Actant\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Noun" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem cat="VP" lu="быть" name="есть" role="есть" /><konst:int_const_elem cat="Noun" msd="Case=Nom" name="NP2" role="Actant" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_вести_в_NP', 'konstruktikon-rus--NP1_вести_в_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"вести\" name=\"вести\"\n        role=\"вести\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Location\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem lu="вести" name="вести" role="вести" /><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem cat="NP" msd="Case=Acc" name="NP2" role="Location" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_иметь_вес_при/в_NP', 'konstruktikon-rus--NP1_иметь_вес_при/в_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Agent\" />\n        <konst:int_const_elem lu=\"иметь\" msd=\"Aspect=Ipf\" name=\"иметь\" /><konst:int_const_elem lu=\"вес\" name=\"вес\" /><konst:int_const_elem lu=\"при/в\" name=\"при/в\" role=\"при/в\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Abl\"\n        name=\"NP\" role=\"Location\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Agent" /><konst:int_const_elem lu="иметь" msd="Aspect=Ipf" name="иметь" /><konst:int_const_elem lu="вес" name="вес" /><konst:int_const_elem lu="при/в" name="при/в" role="при/в" /><konst:int_const_elem cat="NP" msd="Case=Abl" name="NP2" role="Location" /></Sense>', text)
    text = text.replace('<konst:int_const_elem cat="V" lu="пристать"', '<konst:int_const_elem cat="V" lu="приставать"')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\" name=\"NP\"\n        role=\"Agent\" />\n        <konst:int_const_elem cat=\"Particle\" name=\"лишь\" />\n        <konst:int_const_elem cat=\"Particle\" name=\"бы\" />\n        <konst:int_const_elem cat=\"Particle\" name=\"не\" />\n        <konst:int_const_elem cat=\"VP\" msd=\"Mood=Inf\" name=\"VP\"\n        role=\"Action\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP" role="Agent" /><konst:int_const_elem cat="Particle" name="лишь" /><konst:int_const_elem cat="Particle" name="бы" /><konst:int_const_elem cat="VP" msd="Mood=Inf" name="VP" role="Action" /></Sense>', text)
    text = re.sub('<feat att=\"cee\" val=\"не\" />\n        <feat att=\"structure\"\n        val=\"\[root \[obl NP\] \[aux \[advmod лишь\] бы] VP]\" />', '<feat att="structure" val="[root [obl NP] [aux [advmod лишь] бы] VP]" />', text)
    text = text.replace('konstruktikon-rus--NP_Adj_до_NP', 'konstruktikon-rus--NP1_Adj_до_NP2')
    text = text.replace('konstruktikon-rus--NP_VP_(до_NP)', 'konstruktikon-rus--NP1_VP_(до_NP2)')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Agent\" />\n        <konst:int_const_elem cat=\"VP\" msd=\"Verb=Reflexive\"\n        name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem lu=\"до\" name=\"до\" role=\"до\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Agent" /><konst:int_const_elem cat="VP" msd="Verb=Reflexive" name="VP" role="Action" /><konst:int_const_elem lu="до" name="до" role="до" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--куда_NP_до_NP', 'konstruktikon-rus--куда_NP1_до_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Adv\" lu=\"куда\" name=\"куда\"\n        role=\"куда\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Experiencer\" />\n        <konst:int_const_elem cat=\"Pr\" lu=\"до\" name=\"до\"\n        role=\"до\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Goal\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Adv" lu="куда" name="куда" role="куда" /><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP1" role="Experiencer" /><konst:int_const_elem cat="Pr" lu="до" name="до" role="до" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP2" role="Goal" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_далеко_до_NP', 'konstruktikon-rus--NP1_далеко_до_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"далеко\" name=\"далеко\"\n        role=\"далеко\" />\n        <konst:int_const_elem lu=\"до\" name=\"до\" role=\"до\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Standard\" />\n      </Sense>', '</definition><konst:int_const_elem lu="далеко" name="далеко" role="далеко" /><konst:int_const_elem lu="до" name="до" role="до" /><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP1" role="Theme" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP2" role="Standard" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_NP_рознь', 'konstruktikon-rus--NP1_NP2_рознь')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Prototype\" />\n        <konst:int_const_elem lu=\"рознь\" name=\"рознь\"\n        role=\"рознь\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Noun" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem cat="Noun" msd="Case=Dat" name="NP2" role="Prototype" /><konst:int_const_elem lu="рознь" name="рознь" role="рознь" /></Sense>', text)
    text = text.replace('[root NP [nmod NP]] рознь]', '[root NP [nmod NP] рознь]')
    text = text.replace('konstruktikon-rus--Этот-Nom_NP_не_про_NP', 'konstruktikon-rus--Этот_NP_не_про_NP')
    text = text.replace('konstruktikon-rus--Этот_NP_не_про_NP', 'konstruktikon-rus--Этот_NP1_не_про_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Beneficiary\" />\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" />\n        <konst:int_const_elem cat=\"Prep\" lu=\"про\" name=\"про\"\n        role=\"про\" />\n        <konst:int_const_elem lu=\"этот\" msd=\"Case=Nom\" name=\"этот\" role=\"этот\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem cat="NP" msd="Case=Acc" name="NP2" role="Beneficiary" /><konst:int_const_elem lu="не" name="не" role="не" /><konst:int_const_elem cat="Prep" lu="про" name="про" role="про" /><konst:int_const_elem lu="этот" msd="Case=Nom" name="этот" role="этот" /></Sense>', text)
    text = text.replace('konstruktikon-rus--рассказывай_Cl', 'konstruktikon-rus--рассказывай,_Cl')
    text = text.replace('<karp:e n="0" name="рассказывай">Рассказывай</karp:e>', '<karp:e n="0" name="рассказывай,">Рассказывай</karp:e>')
    text = text.replace('konstruktikon-rus--как_VP,_так_и_VP', 'konstruktikon-rus--как_VP1,_так_и_VP2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"как\" name=\"как\" role=\"как\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem cat=\"VP\" name=\"VP\" role=\"Result\" />\n        <konst:int_const_elem lu=\"так\" name=\"так\" role=\"так\" />\n        <konst:int_const_elem lu=\"и\" name=\"и\" role=\"и\" />\n      </Sense>', '</definition><konst:int_const_elem lu="как" name="как" role="как" /><konst:int_const_elem cat="VP" name="VP1" role="Action" /><konst:int_const_elem cat="VP" name="VP2" role="Result" /><konst:int_const_elem lu="так" name="так" role="так" /><konst:int_const_elem lu="и" name="и" role="и" /></Sense>', text)
    text = text.replace('konstruktikon-rus--не_столь(ко)_Adj,_сколь(ко)_Adj', 'konstruktikon-rus--не_столь(ко)_Adj1,_сколь(ко)_Adj2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"не\" name=\"не\" />\n        <konst:int_const_elem lu=\"столь\(ко\)\" name=\"столь\(ко\)\" />\n        <konst:int_const_elem lu=\"сколь\(ко\)\" name=\"сколь\(ко\)\" />\n        <konst:int_const_elem cat=\"Adj\" name=\"Adj\" role=\"Actant\" />\n        <konst:int_const_elem cat=\"Adj\" name=\"Adj\"\n        role=\"Property\" />\n      </Sense>', '</definition><konst:int_const_elem lu="не" name="не" /><konst:int_const_elem lu="столь(ко)" name="столь(ко)" /><konst:int_const_elem lu="сколь(ко)" name="сколь(ко)" /><konst:int_const_elem cat="Adj" name="Adj1" role="Actant" /><konst:int_const_elem cat="Adj" name="Adj2" role="Property" /></Sense>', text)
    text = text.replace('<konst:int_const_elem cat="VP" msd="Tense=Praet" role="Action" />', '<konst:int_const_elem cat="VP" name="VP" msd="Tense=Praet" role="Action" />')
    text = text.replace('konstruktikon-rus--Adv -то_как_Cl!', 'konstruktikon-rus--Adv-то_как_Cl!')
    text = text.replace('<konst:int_const_elem lu="-то" name="-то" role="-то" />', '<konst:int_const_elem lu="-то" name="то" role="-то" />')
    text = text.replace('konstruktikon-rus--NP_не_до_NP', 'konstruktikon-rus--NP1_не_до_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Prep\" lu=\"до\" msd=\"Prep=\"\n        name=\"до\" role=\"до\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Gen\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Experiencer\" />\n        <konst:int_const_elem lu=\"не\" name=\"не\" role=\"не\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Prep" lu="до" msd="Prep=" name="до" role="до" /><konst:int_const_elem cat="NP" msd="Case=Gen" name="NP1" role="Theme" /><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP2" role="Experiencer" /><konst:int_const_elem lu="не" name="не" role="не" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_сделаться_NP/Adj', 'konstruktikon-rus--NP1_сделаться_NP2/Adj')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"сделаться\"\n        msd=\"Aspect=Pf\" name=\"сделаться\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Ins\"\n        name=\"NP\" role=\"Result\" />\n        <konst:int_const_elem cat=\"Adjective\" msd=\"Case=Ins\"\n        name=\"Adj\" role=\"Result\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem lu="сделаться" msd="Aspect=Pf" name="сделаться" /><konst:int_const_elem cat="NP" msd="Case=Ins" name="NP2" role="Result" /><konst:int_const_elem cat="Adjective" msd="Case=Ins" name="Adj" role="Result" /></Sense>', text)
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Num\" msd=\"Case=Nom\"\n        name=\"Num\" role=\"Number\" />\n        <konst:int_const_elem cat=\"NP\" lu=\"год\" msd=\"Case=Gen\"\n        name=\"лет\" role=\"лет\" />\n        <konst:int_const_elem cat=\"VP\" lu=\"дать\" name=\"дать\"\n        role=\"дать\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Dat\"\n        name=\"NP\" role=\"Participant\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Num" msd="Case=Acc" name="Num" role="Number" /><konst:int_const_elem cat="NP" lu="год" msd="Case=Gen" name="лет" role="лет" /><konst:int_const_elem cat="VP" lu="дать" name="дать" role="дать" /><konst:int_const_elem cat="NP" msd="Case=Dat" name="NP" role="Participant" /></Sense>', text)
    text = text.replace('<feat att="cee" val="дать" />', '<feat att="cee" val="дать" /><feat att="cee" val="давать" />')    
    text = text.replace('msd="Clause"', 'msd="Clause="')
    text = text.replace('konstruktikon-rus--NP_VP_в_NP', 'konstruktikon-rus--NP1_VP_в_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"NP\" msd=\"NounType=Nominative\"\n        name=\"NP\" role=\"Agent\" />\n        <konst:int_const_elem cat=\"VP\" msd=\"Verb=Reflexive\"\n        name=\"VP\" role=\"Action\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="NP" msd="NounType=Nominative" name="NP1" role="Agent" /><konst:int_const_elem cat="VP" msd="Verb=Reflexive" name="VP" role="Action" /><konst:int_const_elem lu="в" name="в" role="в" /><konst:int_const_elem cat="NP" msd="Case=Acc" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--что_ни_NP,_то_NP', 'konstruktikon-rus--что_ни_NP1,_то_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem lu=\"что\" name=\"что\" />\n        <konst:int_const_elem lu=\"то\" name=\"то\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem lu=\"ни\" name=\"ни\" />\n        <konst:int_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Set\" />\n      </Sense>', '</definition><konst:int_const_elem lu="что" name="что" /><konst:int_const_elem lu="то" name="то" /><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem lu="ни" name="ни" /><konst:int_const_elem cat="NP" msd="Case=Nom" name="NP2" role="Set" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_и_NP', 'konstruktikon-rus--NP1_и_NP2')
    text = re.sub('</definition>\n        <konst:int_const_elem cat=\"Conjunction\" lu=\"и\" name=\"и\"\n        role=\"и\" />\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:int_const_elem cat=\"Noun\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Theme\" />\n      </Sense>', '</definition><konst:int_const_elem cat="Conjunction" lu="и" name="и" role="и" /><konst:int_const_elem cat="Noun" msd="Case=Nom" name="NP1" role="Theme" /><konst:int_const_elem cat="Noun" msd="Case=Nom" name="NP2" role="Theme" /></Sense>', text)
    text = text.replace('konstruktikon-rus--NP_NP_в_NP', 'konstruktikon-rus--NP1_NP2_в_NP3')
    text = re.sub('</definition>\n        <konst:ext_const_elem cat=\"NP\" msd=\"Case=Ins\"\n        name=\"NP\" role=\"Theme\" />\n        <konst:ext_const_elem cat=\"NP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Experiencer\" />\n        <konst:ext_const_elem name=\"в\" role=\"в\" />\n        <konst:ext_const_elem cat=\"NP\" msd=\"Case=Acc\"\n        name=\"NP\" role=\"Participant\" />\n      </Sense>', '</definition><konst:ext_const_elem cat="NP" msd="Case=Ins" name="NP1" role="Theme" /><konst:ext_const_elem cat="NP" msd="Case=Nom" name="NP2" role="Experiencer" /><konst:ext_const_elem name="в" role="в" /><konst:ext_const_elem cat="NP" msd="Case=Acc" name="NP3" role="Participant" /></Sense>', text)
    text = text.replace('[root [nsubj что] [obl [case с] ним?]] Почему он плачет?', '[root [nsubj что] [obl [case с] ним?] Почему он плачет?]')
    text = text.replace('cat="A"', 'cat="Adj"')
    text = text.replace('cat="ADV"', 'cat="Adv"')
    text = text.replace('cat=" ADV"', 'cat="Adv"')
    text = text.replace('cat="Adverb"', 'cat="Adv"')
    text = text.replace('cat="Action" name="VP" role="VP"', 'cat="VP" name="VP" role="VP"')
    text = text.replace('cat="Action"', 'cat="Clause"')
    text = text.replace('cat="AP"', 'cat="AdjP"')
    text = text.replace('cat="Adjective"', 'cat="Adj"')
    text = text.replace('cat="CONJ"', 'cat="Conjunction"')
    text = text.replace('cat="Conj"', 'cat="Conjunction"')
    text = text.replace('cat="Cl"', 'cat="Clause"')
    text = text.replace('cat="CP" lu="что" name="что"', 'lu="что" name="что"')
    text = text.replace('cat="Conjunctive" lu="или" name="или"', 'cat="Conjunction" lu="или" name="или"')
    text = text.replace('cat="DiscC"', 'cat="Clause"')
    text = text.replace('cat="INTJ"', 'cat="Intj"')
    text = text.replace('cat="N"', 'cat="Noun"')
    text = text.replace('cat="NP2"', 'cat="NP"')
    text = text.replace('cat="AdjP|AdvP"', 'cat="AdjP"')
    text = text.replace('cat="PART"', 'cat="Particle"')
    text = text.replace('cat="Part"', 'cat="Particle"')
    text = text.replace('cat="part"', 'cat="Particle"')
    text = text.replace('cat="PP"', 'cat="Preposition"')
    text = text.replace('cat="Prep"', 'cat="Preposition"')
    text = text.replace('cat="Pr"', 'cat="Preposition"')
    text = text.replace('cat="Prepostion"', 'cat="Preposition"')
    text = text.replace('cat="PRON"', 'cat="Pronoun"')
    text = text.replace('cat="Pron"', 'cat="Pronoun"')
    text = text.replace('cat="Pro"', 'cat="Pronoun"')
    text = text.replace('cat="PronP"', 'cat="PronounP"')
    text = text.replace('cat="Pronominative"', 'cat="PronounP"')
    text = text.replace('cat="Participle"', 'cat="Particle"')
    text = text.replace('cat="NP"', 'cat="NounP"')
    text = text.replace('cat="S"', 'cat="Clause"')
    text = text.replace('cat="Sl"', 'cat="Clause"')
    text = text.replace('cat="Theme" name="Cl" role="Cl"', 'cat="Cl" name="Cl" role="Theme"')
    text = text.replace('cat="V"', 'cat="Verb"')
    text = text.replace('cat="VERB"', 'cat="Verb"')
    text = text.replace('cat="VP"', 'cat="VerbP"')
    text = text.replace('lu="Case=Dat"', 'msd="Case=Dat"')
    text = text.replace('lu="Case=Gen"', 'msd="Case=Gen"')
    text = text.replace('lu="Mood=Inf"', 'msd="Mood=Inf"')
    text = text.replace('lu="Сидеть"', 'lu="сидеть"')
    text = text.replace('lu="Что"', 'lu="что"')
    text = text.replace('role="Cl"', '')
    text = text.replace('Experiecner', 'Experiencer')
    text = text.replace('participant', 'Participant')
    text = text.replace('role="PRON"', '')
    text = text.replace('Situatuon', 'Situation')
    text = text.replace('role="VP"', '')
    text = text.replace('role="c"', 'role="с"')
    text = text.replace('aux="neg"', 'aux="Negative"')
    text = text.replace('aux="negative"', 'aux="Negative"')
    text = text.replace('aux="animate"', 'aux="Animate"')
    for elem in ['facultative', 'plural', 'transitive']:
        text = text.replace('aux="' + elem + '"', 'aux="' + elem.capitalize() + '"')
    text = text.replace('aux="неизменяемая"', 'aux="Invariable"')
    text = text.replace('NounType=Nominative', 'Case=Nom')
    text = text.replace('cat="Cl"', 'cat="Clause"')
    text = text.replace('konstruktikon-rus--NP_пребывать_на/в_NP/у_NP', 'konstruktikon-rus--NP1_пребывать_на/в_NP2/у_NP2')
    text = text.replace('<konst:int_const_elem cat=\"NounP\" msd=\"Case=Nom\"\n        name=\"NP\" role=\"Agent\" />\n        <konst:int_const_elem lu=\"пребывать\"\n        msd=\"Aspect=Ipf\" name=\"пребывать\" />\n        <konst:int_const_elem lu=\"на\" name=\"на\" role=\"на\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NounP\" msd=\"Case=Abl\"\n        name=\"NP\" role=\"Location\" />', '<konst:int_const_elem cat=\"NounP\" msd=\"Case=Nom\"\n        name=\"NP1\" role=\"Agent\" />\n        <konst:int_const_elem lu=\"пребывать\"\n        msd=\"Aspect=Ipf\" name=\"пребывать\" />\n        <konst:int_const_elem lu=\"на\" name=\"на\" role=\"на\" />\n        <konst:int_const_elem lu=\"в\" name=\"в\" role=\"в\" />\n        <konst:int_const_elem cat=\"NounP\" msd=\"Case=Abl\"\n        name=\"NP2\" role=\"Location\" />')
    with open(NAME, 'w', encoding='utf-8') as f:
        f.seek(0)
        f.write(text)
        f.truncate()


def parseXML(xml_file):
    """
    Парсинг XML используя ElementTree
    """

    tree = ET.ElementTree(file=xml_file)
    root = tree.getroot()

    appointments = list(root)
    appt_children = list(appointments[1])[1:]
    
    dct = dict()
    for key in ['lastmodified', 'lastmodifiedBy', 'id',
                'illustration', 'cefr', 'type', 'cee',
                'structure', 'examples', 'rus_definition',
                'eng_definition', 'nor_definition', 'comment',
                'coll', 'cat', 'reference', 'inheritance', 'evokes', 'names']:
        dct[key] = []
    
    langs = {'rus', 'eng', 'nor'}
    for ind, appt_child in enumerate(appt_children):
        tags = list(appt_child)
        for i in range(2):
            tmp = tags[i].attrib
            att = tmp['att']
            if att == 'BCxnID':
                continue
            val = tmp['val']
            dct[att].append(val)
        construction = tags[3].attrib['id'].split('--')[1]
        for symbol in '),?!:;"':
            construction = construction.replace(symbol, '_' + symbol)
        for symbol in '(':
            construction = construction.replace(symbol, symbol + '_')
        con = ''
        for i, word in enumerate(construction.split()):
            if '/' in word:
                if '-' in word.split('/')[0] and '-' in word.split('/')[1] or '-' not in word.split('/')[0] and '-' not in word.split('/')[1]:
                    con += '/'.join(word.split('/')) + ' '
                else:
                    con += word + ' '
            else:
                con += word + ' '
        construction = con.strip()
        construction = construction.split('_')
        construction = ' '.join(construction)
        construction = construction.replace(' ,', ',')
        construction = construction.replace(' )', ')')
        construction = construction.replace('( ', '(')
        construction = construction.replace(' ?', '?')
        construction = construction.replace(' !', '!')
        if construction[0] == '(':
            construction = construction[0] + construction[1].capitalize() + construction[2:] 
        else:
            construction = construction[0].capitalize() + construction[1:] 
        if construction[-1] not in '!?.':
            construction += '.'
        
        dct['id'].append(construction)
        tags = list(tags[3])
        cee = ''
        structure = ''
        comment = ''
        type_ = []
        coll = []
        cat = ''
        reference = ''
        inheritance = ''
        evokes = ''
        i = 0
        fl_ = 0
        flag = 0
        while  i < len(tags) and 'example' not in tags[i].tag:
            tmp = tags[i].attrib
            if 'att' not in tmp:
                i += 1
                continue
            att = tmp['att']
            val = tmp['val']
            if att == 'comment':
                comment += val
                i += 1
                continue
            if att == 'cee':
                cee += val + ' '
                i += 1
                continue
            if att == 'structure':
                structure += val + '~'
                i += 1
                continue
            if att == 'type':
                type_.append(val)
                i += 1
                continue
            if att == 'coll':
                coll.append(val)
                i += 1
                continue
            if att == 'cat':
                cat = val
                i += 1
                continue
            if att == 'reference':
                reference = val
                i += 1
                continue
            if att == 'inheritance':
                inheritance = val
                i += 1
                continue            
            if att == 'evokes':
                evokes = val
                i += 1
                continue
            if att == 'BCxnID':
                i += 1
                continue            
            dct[att].append(val)
            if att == 'cefr':
                flag = 1
            i += 1
        if flag == 0:
            dct['cefr'].append('')
        dct['comment'].append(comment)
        dct['cee'].append(cee[:-1])
        dct['structure'].append(structure[:-1])
        dct['type'].append(type_)
        dct['coll'].append(coll)
        dct['cat'].append(cat)
        dct['reference'].append(reference)
        dct['inheritance'].append(inheritance)
        dct['evokes'].append(evokes)
        examples = []
        while i < len(tags) and 'example' in tags[i].tag:
            subtags = list(tags[i])
            example = ''
            for j, subtag in enumerate(subtags):
                subsubtags = list(subtag)
                if subsubtags:
                    for k, subsubtag in enumerate(subsubtags):
                        if subsubtag.text:
                            attr = subsubtag.attrib
                            if 'name' in attr:
                                example += '[' + '_'.join(str(subsubtag.text).split()) + ']' + '_' + attr['name']
                            else:
                                example += str(subsubtag.text)
                            example += ' '
                elif subtag.text:
                    attr = subtag.attrib
                    if 'name' in attr:
                        example += '[' + '_'.join(str(subtag.text).split()) + ']' + '_' + attr['name']
                    else:
                        example += str(subtag.text)
                    example += ' '
            example = example.replace('\n          ', ' ').strip()
            example = re.sub(r'\[([!―()?…".»a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \"', ' [' + r'\g<1>"' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\" \[([!―()?…»".a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)', ' [' + r'"\g<1>' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\( \[([!―()?…»".a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)', ' [' + r'(\g<1>' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!\"―()?…».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) ,', ' [' + r'\g<1>,' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!\"―()?…».a-zA-Zа-я_А-Яёa-zA-Z-ó,-]*)\]_([()а-яА-Яёa-zA-Z-ó_+,-]*?),', ' [' + r'\g<1>,' + ']' + '_' + r'\g<2>', example)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёa-zA-Z-ó0-9,-]*)\]_([()а-яА-Яёa-zA-Z-0-9_+-,]*?) :', ' [' + r'\g<1>:' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*…)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \!', ' [' + r'\g<1>!' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \?', ' [' + r'\g<1>?' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()…"».a-zA-Zа-я_А-Яёó0-9,-?]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \!', ' [' + r'\g<1>!' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([!()а-яА-Яёa-zA-Zó0-9_+,-]*?) \)', ' [' + r'\g<1>)' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) …', ' [' + r'\g<1>…' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \"!', ' [' + r'\g<1>"!' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'« \[([!―()?»…".a-zA-Zа-я_А-Яёó,-]*)\]_([()а-яА-Яёa-zA-Zó_+,-]*?) ', ' [' + r'«\g<1>' + ']' + '_' + r'\g<2> ', example, re.DOTALL)
            example = re.sub(r'" \[([!―()?»…".a-zA-Zа-я_А-Яёó,-]*)\]_([()а-яА-Яёa-zA-Zó_+,-]*?) ', ' [' + r'"\g<1>' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?…"».a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) »', ' [' + r'\g<1>»' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\(\[([!―()?»…".a-zA-Zа-я_А-Яёó,-]*)\]_([()а-яА-Яёa-zA-Zó_+,-]*?) ', ' [' + r'(\g<1>' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―\)?(…»".a-zA-Zа-я_А-Яёó0-9,-]*)\]_([!\)(а-яА-Яёa-zA-Zó0-9_+,-]*?)\.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'([!―()?….»"a-zA-Zа-яА-Яёa-zA-Zó/_+,-]*?) \.', r' \g<1>.', example, re.DOTALL)
            example = re.sub(r'\[([!―()?»"….a-zA-Zа-я_А-Яёó0-9.,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)\.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?.»…"a-zA-Zа-я_А-Яёó0-9.,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)\.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?.»…"a-zA-Zа-я_А-Яёó0-9.,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)\!', ' [' + r'\g<1>!' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?.»…"a-zA-Zа-я_А-Яёó0-9,.-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)\"', ' [' + r'\g<1>"' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?.»…"a-zA-Zа-я_А-Яёó0-9,.-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)―', ' [' + r'\g<1>―' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?»…".a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?)»', ' [' + r'\g<1>»' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = re.sub(r'\[([!―()?»…".a-zA-Zа-я_А-Яёó0-9,-]*)\]_([()а-яА-Яёa-zA-Zó0-9_+,-]*?) \"', ' [' + r'\g<1>"' + ']' + '_' + r'\g<2>', example, re.DOTALL)
            example = example.replace(' , ', ', ')
            example = example.replace(' ! ', '! ')
            
            if example:
                examples.append(example)
            i += 1
        dct['examples'].append(examples)
        
        st_langs = set()
        while i < len(tags) and tags[i].tag == 'definition':
            subtags = list(tags[i])
            definition = ''
            for k, subtag in enumerate(subtags):
                if subtag.text:
                    attr = subtag.attrib
                    if 'name' in attr:
                        definition += '[' + '_'.join(str(subtag.text).split()) + ']' + '_' + attr['name']
                    else:
                        definition += str(subtag.text)
                    definition += ' '
            attr = tags[i].attrib
            
            definition = definition.replace('\n          ', ' ').strip()            
            definition = re.sub(r'([a-zа-я-])\.', r'\g<1> .', definition)            
            definition = re.sub(r' \[([’"?()æøåÆØÅа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Z-ó]*?) ,', ' [' + r'\g<1>,' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Z-ó]*?),', ' [' + r'\g<1>,' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Z-ó]*?) :', ' [' + r'\g<1>:' + ']' + '_' + r'\g<2>', definition)            
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?) \.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*) \.\]_([а-яА-Яa-zA-Zó]*?)', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?) \!', ' [' + r'\g<1>!' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?) ;', ' [' + r'\g<1>;' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?) \?', ' [' + r'\g<1>?' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?) \)', ' [' + r'\g<1>)' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \(\[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Zó/,]*)\]_([а-яА-Яa-zA-Zó]*?) ', ' [' + r'(\g<1>' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?)’,', ' [' + r'\g<1>’,' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?)’', ' [' + r'\g<1>’' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?)\.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', definition)
            definition = re.sub(r' ([’"æøåÆØÅа()а-яА-ЯёЁa-zA-Zó/,]*?) \.', r' \g<1>.', definition)
            definition = re.sub(r' ([’"æøåÆØÅа()а-яА-ЯёЁa-zA-Z-ó/,]*?) ,', r' \g<1>,', definition)
            definition = re.sub(r' \" \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Zó/,]*)\]_([а-яА-Яa-zA-Zó]*?) ', ' [' + r'"\g<1>' + ']' + '_' + r'\g<2> ', definition)
            definition = re.sub(r' \( \[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Zó/,]*)\]_([а-яА-Яa-zA-Zó]*?) ', ' [' + r'(\g<1>' + ']' + '_' + r'\g<2> ', definition)            
            definition = re.sub(' " (.*?) " ', r'"\g<1>"', definition)
            definition = definition.replace('“ ', '“')
            definition = re.sub(r' \“\[([’"?()æøåÆØÅаа-я_А-ЯёЁa-zA-Zó/,]*)\]_([а-яА-Яa-zA-Zó]*?) ', ' [' + r'“\g<1>' + ']' + '_' + r'\g<2> ', definition)
            definition = definition.replace(' .', '.')
            definition = definition.replace(' / ', '/')
            definition = definition.replace(' /', '/')
            definition = re.sub(r' \[([()æøåÆØÅаа-я_А-Яa-zA-Z-ó/,]*)\]_([а-яА-Яa-zA-Zó]*?)\.', ' [' + r'\g<1>.' + ']' + '_' + r'\g<2>', definition)

            if not attr:
                dct['rus_definition'].append(definition)
                st_langs.add('rus')
            else:
                if attr['{http://www.w3.org/XML/1998/namespace}lang'] == 'eng':
                    dct['eng_definition'].append(definition)
                    st_langs.add('eng')
                if attr['{http://www.w3.org/XML/1998/namespace}lang'] == 'nor':
                    dct['nor_definition'].append(definition)
                    st_langs.add('nor')
            i += 1
            
        for lang in langs - st_langs:
            dct[lang + '_definition'].append('')
        
        dct['names'].append(dict())
        for j in range(i, len(tags)):
            if 'name' not in tags[j].attrib:
                continue
            name = tags[j].attrib['name'].lower()
            dct['names'][-1][name] = dict()
            for key, value in tags[j].attrib.items():
                if key != 'name':
                    dct['names'][-1][name][key] = value
        
        for key1, value1 in dct['names'][ind].items():
            s = ''
            for key2, value2 in value1.items():
                s += key2 + ': ' + value2 + '\n'
            dct['names'][ind][key1] = s.strip('\n')
        
    for i, elem in enumerate(dct['lastmodified']):
        dct['lastmodified'][i] = dct['lastmodified'][i].split('T')
    for i, elem in enumerate(dct['illustration']):
        dct['illustration'][i] = dct['illustration'][i].strip()[0].capitalize() + dct['illustration'][i].strip()[1:]
        if dct['illustration'][i][-1] not in '.!?;':
            dct['illustration'][i] += '.'
    for i, elem in enumerate(dct['cefr']):
        dct['cefr'][i] = dct['cefr'][i].lower()
    dct['eng_definition'][30] = dct['eng_definition'][30].replace('быть', '"быть"')
    dct['examples'][171][3] = 'У него [в]_в [ушах]_Location до сих пор стоял [стон]_Theme раненого.'
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(dct, f)


if __name__ == '__main__':
    app.run(debug=True)
