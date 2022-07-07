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
somme_profit_list = {}
user_date_initial = {}
profitabilite_minute = []
k = 0
commission = 0.15

f = open('profit_2022_7.txt', 'r', encoding='UTF-8')
_lines = f.readlines()
lines = []
i = 0
pro = 0

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
                if key in somme_profit.keys():
                    t = evaluation * ((somme[key] + somme_profit[key]) / (sum(somme.values()) + sum(somme_profit.values())))
                    somme_profit[key] += t
                    somme_profit_list[key].append(somme_profit[key])
                else:
                    t = evaluation * somme[key] / sum(somme.values())
                    somme_profit[key] = t
                    user_date_initial[key] = date_initial
                    somme_profit_list[key] = [somme_profit[key]]

            for key in somme:
                rangee = []
                rangee.append(key)
                rangee.append(locale.format_string("%d", evaluation * somme[key] / sum(somme.values()), grouping=True))
                rangee.append(locale.format_string("%d", somme[key], grouping=True))
                #rangee.append(locale.format_string("%d", somme_profit[key], grouping=True))
                rangee.append(locale.format_string("%d", somme_profit[key] * (1 - commission), grouping=True))
                rangee.append(locale.format_string("%f", round(somme_profit[key] / somme[key] * 100, 6), grouping=True))
                rangee.append(user_date_initial[key])
                list_rangee.append(rangee)

            print("누적 원금 : " + locale.format_string("%d", sum(somme.values()), grouping=True) + "원")
            print("누적 평가손익 : " + locale.format_string("%d", sum(somme_profit.values()), grouping=True) + "원")
            pro += profitabilite
            print("수탁보수액 : " + locale.format_string("%d", sum(somme_profit.values()) * commission, grouping=True) + "원")
            print("단순누적 수익률(복리 미가산) : " + str(round(pro, 6)) + "%")
            
            print("전이벤트대비 평가손익 : " + locale.format_string("%d", evaluation, grouping=True) + '원')
            print("시간당 평균 평가손익 : " + locale.format_string("%d", evaluation / diff_second * 3600, grouping=True) + '원')
            print("수익률 : " + str(round(profitabilite, 6)) + "%")
            #print("시간당 평균 수익률 : " + locale.format_string("%f", profitabilite / diff_second * 3600, grouping=True) + '%')

            df = pd.DataFrame(list_rangee, columns = ['채권자', '당해 평가손익', '원금 합계', '평가손익(공제 후)', '수익률(%)', '최초자산편입일'])
            print(df.to_markdown()) 
            print('\n')
    else:
        list_donnee = lines[p].split(' ')
        date_initial = list_donnee[0]
        temp_initial = datetime.strptime(date_initial, '%Y.%m.%d.%H:%M')
        date_final = list_donnee[1]
        temp_final = datetime.strptime(date_final, '%Y.%m.%d.%H:%M')
        diff_second = (temp_final - temp_initial).total_seconds()

        event = int(list_donnee[2])
        montant_initial = int(list_donnee[3])
        montant_final = int(list_donnee[4])

        print(date_initial + ' ~ ' + date_final + ' (' + str(temp_final - temp_initial) + ', time_diff=' + str(diff_second) + ')' )
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

        for k in range(int(diff_second / 60)):
            profitabilite_minute.append(profitabilite)

        if event >= 2:
            for key in somme:
                if key in somme_profit.keys():
                    t = evaluation * ((somme[key] + somme_profit[key]) / (sum(somme.values()) + sum(somme_profit.values())))
                    somme_profit[key] += t
                    somme_profit_list[key].append(somme_profit[key])
                else:
                    t = evaluation * somme[key] / sum(somme.values())
                    somme_profit[key] = t
                    somme_profit_list[key] = [somme_profit[key]]

            list_rangee = []
            for key in somme:
                rangee = []
                rangee.append(key)
                rangee.append(locale.format_string("%d", evaluation * somme[key] / sum(somme.values()), grouping=True))
                rangee.append(locale.format_string("%d", somme[key], grouping=True))
                #rangee.append(locale.format_string("%d", somme_profit[key], grouping=True))
                rangee.append(locale.format_string("%d", somme_profit[key] * (1 - commission), grouping=True))
                rangee.append(locale.format_string("%f", round(somme_profit[key] / somme[key] * 100, 6), grouping=True))
                rangee.append(user_date_initial[key])
                list_rangee.append(rangee)

            print("누적 원금 : " + locale.format_string("%d", sum(somme.values()), grouping=True) + "원")
            print("누적 평가손익 : " + locale.format_string("%d", sum(somme_profit.values()), grouping=True) + "원")
            pro += profitabilite
            print("수탁보수액 : " + locale.format_string("%d", sum(somme_profit.values()) * commission, grouping=True) + "원")
            print("단순누적 수익률(복리 미가산) : " + str(round(pro, 6)) + "%")

            print("전이벤트대비 평가손익 : " + locale.format_string("%d", evaluation, grouping=True) + '원')
            print("시간당 평균 평가손익 : " + locale.format_string("%d", evaluation / diff_second * 3600, grouping=True) + '원')
            print("수익률 : " + str(round(profitabilite, 6)) + "%")
            #print("시간당 평균 수익률 : " + locale.format_string("%f", profitabilite / diff_second * 3600, grouping=True) + '%')

            df2 = pd.DataFrame(list_rangee, columns = ['채권자', '당해 평가손익', '원금 합계', '평가손익(공제 후)', '수익률(%)', '최초자산편입일'])
            print(df2.to_markdown()) 
            print('\n')

evaluation_jour = []
for p in range(int(len(profitabilite_minute) / 1440)):
    somme = 0
    for q in range(1440):
        somme += profitabilite_minute[p * 1440 + q]
    evaluation_jour.append(somme / 1440)

#print(len(evaluation_jour))
#print(evaluation_jour)
