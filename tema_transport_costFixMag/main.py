import numpy as np
import time
import pandas as pd
import os
import re


def citeste_date_din_fisier(nume_fisier):
    with open(nume_fisier, 'r') as f:
        continut = f.read()

    # Extrage datele de intrare din fișier
    d = int(re.search(r'd\s*=\s*(\d+);', continut).group(1))
    r = int(re.search(r'r\s*=\s*(\d+);', continut).group(1))

    SC = list(map(int, re.search(r'SCj\s*=\s*\[([^\]]+)\];', continut).group(1).split()))
    D = list(map(int, re.search(r'Dk\s*=\s*\[([^\]]+)\];', continut).group(1).split()))

    C = np.array(
        [list(map(int, linie.split())) for linie in re.search(r'Cjk\s*=\s*\[\[(.*?)\]\];', continut, re.DOTALL)
         .group(1).strip().replace(']', '').replace('[', '').split('\n')], dtype=float)

    F = np.array(
        [list(map(int, linie.split())) for linie in re.search(r'Fjk\s*=\s*\[\[(.*?)\]\];', continut, re.DOTALL)
         .group(1).strip().replace(']', '').replace('[', '').split('\n')], dtype=float)

    return d, r, SC, D, C, F


def metoda_minim_matrice(d, r, SC, D, C, F):
    fluxuri = np.zeros((d, r), dtype=float)
    cerinte = np.array(D, dtype=float)
    capacitati = np.array(SC, dtype=float)

    start_time = time.time()
    iteration = 0

    while np.any(cerinte > 0):  # Continuăm până când toate cerințele sunt îndeplinite
        iteration += 1

        # Verifică dacă cerințele magazinelor depășesc capacitățile depozitelor
        if np.sum(cerinte) > np.sum(capacitati):
            print("Eroare: Cerințele magazinelor depășesc capacitățile depozitelor.")
            return float('inf'), fluxuri, time.time() - start_time, iteration

        # Calculăm costul total pentru fiecare celulă
        cost_total = C + F
        cost_total[:, cerinte == 0] = np.inf  # Magazinele fără cerințe

        # Verificăm dacă toate costurile sunt infinit
        if np.all(cost_total == np.inf):
            print("Eroare: Nu există perechi valide pentru alocare!")
            print(f"Capacități depozite rămase: {capacitati}")
            print(f"Cerințe magazine rămase: {cerinte}")
            return float('inf'), fluxuri, time.time() - start_time, iteration

        # Găsim poziția (i, j) cu cost minim
        i, j = np.unravel_index(np.argmin(cost_total, axis=None), cost_total.shape)

        # Determinăm cantitatea care poate fi alocată
        alocare = min(capacitati[i], cerinte[j])

        # Verificăm dacă există o alocare validă
        if alocare == 0:
            print("Nu există alocări valabile în această iterație.")
            break

        # Actualizăm fluxurile și resturile
        fluxuri[i, j] = alocare
        capacitati[i] -= alocare
        cerinte[j] -= alocare

        # Depozitul sau magazinul epuizat este setat la infinit
        if capacitati[i] == 0:
            cost_total[i, :] = np.inf
        if cerinte[j] == 0:
            cost_total[:, j] = np.inf

        # Debugging: Afișăm detalii suplimentare
        print(f"Iterația {iteration}: Capacități depozite: {capacitati}")
        print(f"Cerințe magazine: {cerinte}")
        print(f"Fluxuri actualizate:\n{fluxuri}")

        if iteration > 10000:  # Prevenirea unui blocaj infinit
            print("Algoritmul a depășit numărul maxim de iterații.")
            return float('inf'), fluxuri, time.time() - start_time, iteration

    cost_total_min = np.sum(fluxuri * C) + np.sum((fluxuri > 0) * F)
    elapsed_time = time.time() - start_time
    return cost_total_min, fluxuri, elapsed_time, iteration


def scrie_rezultate_in_excel(df_rezultate, fisier_nou):
    if os.path.exists(fisier_nou):
        with pd.ExcelWriter(fisier_nou, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            df_existent = pd.read_excel(fisier_nou, sheet_name='Rezultate')
            df_combined = pd.concat([df_existent, df_rezultate], ignore_index=True)
            df_combined.to_excel(writer, sheet_name='Rezultate', index=False)
    else:
        with pd.ExcelWriter(fisier_nou, engine='openpyxl') as writer:
            df_rezultate.to_excel(writer, sheet_name='Rezultate', index=False)


def rezolva_problema_transport(nume_fisier):
    d, r, SC, D, C, F = citeste_date_din_fisier(nume_fisier)

    print(f"d = {d}, r = {r}")
    print(f"SC = {SC}")
    print(f"D = {D}")
    print(f"C =\n{C}")
    print(f"F =\n{F}")

    cost_total, fluxuri, elapsed_time, numar_iteratii = metoda_minim_matrice(d, r, SC, D, C, F)

    print(f"Fișierul: {nume_fisier}")
    print(f"Costul total minim: {cost_total}")
    print(f"Timp de execuție: {elapsed_time:.4f} secunde")
    print(f"Numărul de iterații: {numar_iteratii}")

    date_rezultate = {
        "Nume fișier": [nume_fisier],
        "Cost minim": [cost_total],
        "Timp execuție (sec)": [elapsed_time],
        "Număr iterații": [numar_iteratii],
        "Status": ["solved" if cost_total < float('inf') else "unsolved"],
    }

    df_rezultate = pd.DataFrame(date_rezultate)
    fisier_nou = 'rezultate_transport_FCR.xlsx'
    scrie_rezultate_in_excel(df_rezultate, fisier_nou)


# Testare cu fișier de exemplu
rezolva_problema_transport("Lab01_FCR_medium_01.dat")
