# -*- coding: utf-8 -*-

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
            print("------------")
            for key in somme:
                t = int(somme[key] * profitabilite / 100)
                print(key + ' : '+ str(t))
                if key in somme_profit.keys():
                    somme_profit[key] += t
                else:
                    somme_profit[key] = t
            print("------------")
            print(somme)
            print(somme_profit)
            print("총원금 : " + str(sum(somme.values())))
            print("총 평가손익 : " + str(sum(somme_profit.values())))
            print('\n')
    else:
        list_donnee = lines[p].split(' ')
        date_initial = list_donnee[0]
        event = int(list_donnee[1])
        montant_initial = int(list_donnee[2])
        montant_final = int(list_donnee[3])

        print(date_initial)
        if event == 1:
            print("입금")
        elif event == 2:
            print("운용자 임의")
        elif event == 3:
            print("만기 도래")
        print("초기운용금액 : " + str(montant_initial))
        print("말기운용금액 : " + str(montant_final))


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

        print("전이벤트대비 평가손익 : " + str(evaluation))
        print("수익률 : " + str(round(profitabilite, 6)) + "%")

        if event >= 2:
            print('\n')

