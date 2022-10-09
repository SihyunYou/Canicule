valeurs = [698, 707, 695, 699, 710, 720, 705, 839, 766, 730]

p = sum(valeurs[:-2]) / (len(valeurs) - 1)
k = 2 / (len(valeurs))
for i in range(2, len(valeurs)):
	p = k * valeurs[i] + (1 - k) * p
e = p
print(e)