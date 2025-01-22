import re
import os
import numpy as np
import pandas as pd
import time
from scipy.optimize import linprog

def citeste_date_din_fisier(nume_fisier):
    with open(nume_fisier, 'r') as f:
        continut = f.read()

    # Verificăm conținutul fișierului citit
    #print("Conținutul fișierului:")
    #print(continut)
    #print(" ")

    # Extragem numărul de depozite și magazine
    try:
        d = int(re.search(r'd\s*=\s*(\d+);', continut).group(1))
        r = int(re.search(r'r\s*=\s*(\d+);', continut).group(1))
    except AttributeError:
        raise ValueError("Nu am găsit numărul de depozite (d) sau numărul de magazine (r) în fișier.")

    #print(f"Numărul de depozite (d): {d}")
    #print(f"Numărul de magazine (r): {r}")

    # Extragem capacitățile depozitelor (SC)
    try:
        SC = list(map(int, re.search(r'SCj\s*=\s*\[([^\]]+)\];', continut).group(1).split()))
    except AttributeError:
        raise ValueError("Nu am găsit datele pentru capacitățile depozitelor (SCj) în fișier.")
    #print(f"Capacitățile depozitelor (SCj): {SC}")

    # Extragem cerințele magazinelor (Dk)
    try:
        D = list(map(int, re.search(r'Dk\s*=\s*\[([^\]]+)\];', continut).group(1).split()))
    except AttributeError:
        raise ValueError("Nu am găsit datele pentru cerințele magazinelor (Dk) în fișier.")
    #print(f"Cerințele magazinelor (Dk): {D}")

    # Extragem costurile (Cjk)
    try:
        C_match = re.search(r'Cjk\s*=\s*\[\[([\s\S]*?)\]\];', continut)
        if not C_match:
            raise ValueError("Nu am găsit matricea de costuri (Cjk) în fișier.")
        C_str = C_match.group(1)
        # Curățăm șirul pentru a elimina parantezele pătrate
        C_str = C_str.replace('[', '').replace(']', '')
        # Reconstruim matricea combinând liniile incomplete
        C_rows = []
        temp_row = []
        for line in C_str.strip().split('\n'):
            # Convertim linia curentă în numere întregi
            values = list(map(int, line.split()))
            temp_row.extend(values)  # Adăugăm valorile la linia temporară
            if len(temp_row) == r:  # Dacă linia temporară are lungimea corectă
                C_rows.append(temp_row)
                temp_row = []  # Resetăm linia temporară
        if temp_row:  # Dacă mai există date rămase, semnalăm eroarea
            raise ValueError(f"Datele din matricea Cjk sunt incomplete: {temp_row}")
    except Exception as e:
        raise ValueError(f"Eroare la citirea matricei de costuri (Cjk): {e}")

    # Construim matricea numpy
    try:
        C = np.array(C_rows)
        #print(f"Dimensiunile matricei inițiale C: {C.shape}")
    except Exception as e:
        raise ValueError(f"Eroare la construirea matricei C: {e}")

    # Redimensionăm matricea C la (10, 50), dacă este necesar
    if C.shape != (10, 50):
        #print(f"Redimensionăm matricea C la dimensiunile (10, 50).")
        C = C[:10, :50]  # Tăiem la dimensiunea dorită, dacă este nevoie.

    #print(f"Dimensiunile matricei finale C: {C.shape}")
    return d, r, SC, D, C

# Exemplu de utilizare
nume_fisier = 'Lab01_simple_large_01.dat'  # Înlocuiește cu calea către fișierul tău
try:
    d, r, SC, D, C = citeste_date_din_fisier(nume_fisier)
    #print("Datele au fost citite cu succes.")
    #print("Dimensiuni matrice C:", C.shape)
    #print(C)
except Exception as e:
    print(f"Eroare: {e}")

def metoda_north_west_corner(d, r, SC, D, C):
    # Creăm o matrice de fluxuri inițială (toate zero)
    fluxuri = np.zeros((d, r))

    # Copiem cerințele și capacitățile
    cerinte = D.copy()
    capacitati = SC.copy()

    # Măsurăm timpul de execuție
    start_time = time.time()

    # Iterăm până când toate cerințele și capacitățile sunt îndeplinite
    i = 0  # indexul depozitului curent
    j = 0  # indexul magazinului curent
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
rezolva_problema_transport("Lab01_simple_large_25.dat")