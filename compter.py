# -*- coding: utf-8 -*-
import pandas as pd
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
import datetime
from datetime import datetime
from datetime import timedelta
import time

somme = {}
somme_profit = {}
date_initial = 0
date_final = 0 

f = open('profit_2022_1.txt', 'r', encoding='UTF-8')
_lines = f.readlines()
lines = []
i = 0

for p in range(len(_lines)):
    if _lines[p][0] != '#':
        if _lines[p][-1] == '\n':
            lines.append(_lines[p][:-1])
        else:
            lines.append(_lines[p])

for p in range(len(lines)):
    if lines[p][0] == '\t':
        list_donnee = lines[p][1:].split(' ')
        qui = list_donnee[0]
        montant_recu = int(list_donnee[1])

        if qui in somme.keys():
            somme[qui] += montant_recu
        else:
            somme[qui] = montant_recu

        if p + 1 < len(lines) and lines[p + 1][0] != '\t' or p + 1 == len(lines):
            list_rangee = []

            for key in somme:
                t = evaluation * somme[key] / sum(somme.values())
                if key in somme_profit.keys():
                    somme_profit[key] += t
                else:
                    somme_profit[key] = t

            for key in somme:
                rangee = []
                rangee.append(key)
                rangee.append(locale.format_string("%d", evaluation * somme[key] / sum(somme.values()), grouping=True))
                rangee.append(locale.format_string("%d", somme[key], grouping=True))
                rangee.append(locale.format_string("%d", somme_profit[key], grouping=True))
                list_rangee.append(rangee)

            print("누적 원금 : " + locale.format_string("%d", sum(somme.values()), grouping=True) + "원")
            print("누적 평가손익 : " + locale.format_string("%d", sum(somme_profit.values()), grouping=True) + "원")

            df = pd.DataFrame(list_rangee, columns = ['채권자', '당해 평가손익', '원금 합계', '평가손익 합계'])
            print(df.to_markdown()) 
            print('\n')
    else:
        list_donnee = lines[p].split(' ')
        date_initial = list_donnee[0]
        temp_initial = datetime.strptime(date_initial, '%Y.%m.%d.%H:%M')
        date_final = list_donnee[1]
        temp_final = datetime.strptime(date_final, '%Y.%m.%d.%H:%M')
        diff_timestamp = int(time.mktime(temp_final.timetuple()) - time.mktime(temp_initial.timetuple()))

        event = int(list_donnee[2])
        montant_initial = int(list_donnee[3])
        montant_final = int(list_donnee[4])

        print(date_initial + ' ~ ' + date_final + ' (' + str(temp_final - temp_initial) + ', time_diff=' + str(diff_timestamp) + ')' )
        i += 1
        if event == 1:
            print("이벤트 " + str(i) + " : 입출금")
        elif event == 2:
            print("이벤트 " + str(i) + " : 운용자 임의")
        elif event == 3:
            print("이벤트 " + str(i) + " : 만기 도래")
        print("운용금액(초기/말기) : " + locale.format_string("%d", montant_initial, grouping=True) + '원 ~ ' + locale.format_string("%d", montant_final, grouping=True) + '원')

        evaluation = montant_final - montant_initial
        profitabilite = evaluation / montant_initial * 100

        if event >= 2:
            for key in somme:
                t = evaluation * somme[key] / sum(somme.values())
                print(key + ' : '+ str(t))
                if key in somme_profit.keys():
                    somme_profit[key] += t
                else:
                    somme_profit[key] = t

        print("전이벤트대비 평가손익 : " + locale.format_string("%d", evaluation, grouping=True) + '원')
        print("시간당 평균 평가손익 : " + locale.format_string("%d", evaluation / diff_timestamp * 3600, grouping=True) + '원')
        print("수익률 : " + str(round(profitabilite, 6)) + "%")
        #print("시간당 평균 수익률 : " + locale.format_string("%f", profitabilite / diff_timestamp * 3600, grouping=True) + '%')
        if event >= 2:
            print('\n')

