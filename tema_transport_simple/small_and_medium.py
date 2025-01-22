import numpy as np
import time
import pandas as pd
import re
import os

def citeste_date_din_fisier(nume_fisier):
    with open(nume_fisier, 'r') as f:
        continut = f.read()

    # Extrage numărul de depozite și magazine
    d = int(re.search(r'd\s*=\s*(\d+);', continut).group(1))
    r = int(re.search(r'r\s*=\s*(\d+);', continut).group(1))

    # Extrage capacitățile depozitelor
    SC = list(map(int, re.search(r'SCj\s*=\s*\[([^\]]+)\];', continut).group(1).split()))

    # Extrage cerințele magazinelor
    D = list(map(int, re.search(r'Dk\s*=\s*\[([^\]]+)\];', continut).group(1).split()))

    # Extrage costurile Cjk
    C_match = re.search(r'Cjk\s*=\s*\[\[(.*?)\]\];', continut, re.DOTALL)

    C_str = C_match.group(1).strip()
    C_str = C_str.replace(']', '').replace('[', '').strip()  # curățăm datele
    C = np.array([list(map(int, linie.split())) for linie in C_str.split('\n')])

    return d, r, SC, D, C

def metoda_north_west_corner(d, r, SC, D, C):
    # Creăm o matrice de fluxuri inițială (toate zero)
    fluxuri = np.zeros((d, r))

    # Copiem cerințele și capacitățile pentru a le manipula
    cerinte = D.copy()
    capacitati = SC.copy()

    # Măsurăm timpul de execuție
    start_time = time.time()

    # Iterăm până când toate cerințele și capacitățile sunt îndeplinite
    i = 0  # Depozite
    j = 0  # Magazine
    numar_iteratii = 0  # Numărul de iterații

    while i < d and j < r:
        # Alocăm marfa minimă posibilă
        alocare = min(capacitati[i], cerinte[j])
        fluxuri[i][j] = alocare

        # Reducem cerințele și capacitățile
        cerinte[j] -= alocare
        capacitati[i] -= alocare

        # Dacă cerința magazinului s-a îndeplinit, trecem la următorul magazin
        if cerinte[j] == 0:
            j += 1

        # Dacă capacitatea depozitului s-a îndeplinit, trecem la următorul depozit
        if capacitati[i] == 0:
            i += 1

        numar_iteratii += 1

    # Calculăm costul total
    cost_total = np.sum(fluxuri * C)

    # Timpul de execuție
    elapsed_time = time.time() - start_time

    return cost_total, fluxuri, elapsed_time, numar_iteratii

def scrie_rezultate_in_excel(df_rezultate, fisier_nou):
    # Verifică dacă fișierul există deja
    if os.path.exists(fisier_nou):
        # Dacă fișierul există, adaugă rezultatele la sfârșit fără a adăuga header-ul
        with pd.ExcelWriter(fisier_nou, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            # Citim datele existente și le combinăm cu cele noi
            df_existent = pd.read_excel(fisier_nou, sheet_name='Rezultate')
            df_combined = pd.concat([df_existent, df_rezultate], ignore_index=True)

            # Eliminăm coloanele goale sau cu valori NA
            df_existent = df_existent.dropna(axis=1, how='all')
            df_rezultate = df_rezultate.dropna(axis=1, how='all')

            # Scriem datele combinate
            df_combined.to_excel(writer, sheet_name='Rezultate', index=False)
    else:
        # Dacă fișierul nu există, creează-l și scrie datele
        with pd.ExcelWriter(fisier_nou, engine='openpyxl') as writer:
            df_rezultate.to_excel(writer, sheet_name='Rezultate', index=False)

def rezolva_problema_transport(nume_fisier):
    # Citirea datelor din fișier
    d, r, SC, D, C = citeste_date_din_fisier(nume_fisier)

    # Apelăm metoda North-West Corner
    cost_total, fluxuri, elapsed_time, numar_iteratii = metoda_north_west_corner(d, r, SC, D, C)

    # Afișăm rezultatele
    print(f"Fișierul: {nume_fisier}")
    print(f"Costul total minim: {cost_total}")
    print(f"Numărul de iterații: {numar_iteratii}")
    print(f"Timp de execuție: {elapsed_time} secunde")

    # Salvăm rezultatele într-un DataFrame
    date_rezultate = {
        "Nume fișier": [nume_fisier],
        "Cost minim": [cost_total],
        "Număr de iterații": [numar_iteratii],
        "Timp execuție (sec)": [elapsed_time],
        "Status": ["solved" if cost_total < float('inf') else "unsolved"],
    }

    df_rezultate = pd.DataFrame(date_rezultate)

    # Numele fișierului unde vor fi salvate rezultatele
    fisier_nou = 'rezultate_transport.xlsx'

    # Apelăm funcția de salvare a rezultatelor în Excel
    scrie_rezultate_in_excel(df_rezultate, fisier_nou)


# Testează funcția
rezolva_problema_transport("Lab01_simple_small_25.dat")
