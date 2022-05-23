# -*- coding: utf-8 -*-
import pandas as pd
import locale
locale.setlocale(locale.LC_ALL, 'en_US')

somme = {}
somme_profit = {}

f = open('profit_2022_1.txt', 'r', encoding='UTF-8')
_lines = f.readlines()
lines = []
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
                t = int(somme[key] * profitabilite / 100)
                if key in somme_profit.keys():
                    somme_profit[key] += t
                else:
                    somme_profit[key] = t

            for key in somme:
                rangee = []
                rangee.append(key)
                rangee.append(locale.format_string("%d", int(somme[key] * profitabilite / 100), grouping=True))
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
        date_final = list_donnee[1]
        event = int(list_donnee[2])
        montant_initial = int(list_donnee[3])
        montant_final = int(list_donnee[4])

        print(date_initial + ' ~ ' + date_final)
        if event == 1:
            print("이벤트 : 입금")
        elif event == 2:
            print("이벤트 : 운용자 임의")
        elif event == 3:
            print("이벤트 : 만기 도래")
        print("운용금액(초기/말기) : " + locale.format_string("%d", montant_initial, grouping=True) + '원 ~ ' + locale.format_string("%d", montant_final, grouping=True) + '원')

        evaluation = montant_final - montant_initial
        profitabilite = evaluation / montant_initial * 100

        if event >= 2:
            for key in somme:
                t = int(somme[key] * profitabilite / 100)
                print(key + ' : '+ str(t))
                if key in somme_profit.keys():
                    somme_profit[key] += t
                else:
                    somme_profit[key] = t

        print("전이벤트대비 평가손익 : " + locale.format_string("%d", evaluation, grouping=True) + '원')
        print("수익률 : " + str(round(profitabilite, 6)) + "%")

        if event >= 2:
            print('\n')

