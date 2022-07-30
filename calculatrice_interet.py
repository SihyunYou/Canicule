import sys
from datetime import datetime
import math

# (1+j)^d = r/c solution for the variable j
# j = (r/c)^(1/d) - 1

capital = int(sys.argv[1])
interet_annee = int(sys.argv[2]) / 100
date_debut = datetime.strptime(sys.argv[3], "%Y%m%d")
date_fin = datetime.strptime(sys.argv[4], "%Y%m%d")
date_diff = date_fin - date_debut
days = date_diff.days + 1
remboursement = capital * (1 + interet_annee * days / 365)
interet_jour = pow(remboursement / capital, 1 / days) - 1

print("interet_jour : ", interet_jour)
print("date_diff : ", days)
print(int(round(capital * pow(1 + interet_jour, days), 1)))