import numpy as np
import pandas

df = pandas.read_excel('./meanprofile_MSD.xls')

acquisti = df['nanmean_CNOR_AcquistiMWh']
acquistiKWh = [acquisti[i]/1000 for i in range(len(acquisti))]

acquistiFinal = []
    
for i in range(24):
    acquistiFinal.append(acquistiKWh[i])
    acquistiFinal.append(acquistiKWh[i])
    acquistiFinal.append(acquistiKWh[i])
    acquistiFinal.append(acquistiKWh[i])

acquistiFinal = np.asarray(acquistiFinal)
np.save("Profili/Prezzi_mercato_test/acquistiFinal.npy", acquistiFinal)


print(acquistiKWh)
print(acquistiFinal)

vendite = df['nanmean_CNOR_VenditeMWh']
venditeKWh = [vendite[i]/1000 for i in range(len(vendite))]

venditeFinal = []

for i in range(24):
    venditeFinal.append(venditeKWh[i])
    venditeFinal.append(venditeKWh[i])
    venditeFinal.append(venditeKWh[i])
    venditeFinal.append(venditeKWh[i])

venditeFinal = np.asarray(venditeFinal)
np.save("Profili/Prezzi_mercato_test/venditeFinal.npy", venditeFinal)

print(venditeKWh)
print(venditeFinal)
