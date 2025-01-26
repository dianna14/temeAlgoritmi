import numpy as np
import time
import pandas as pd
import os
import re

def read_data_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Verifică numărul de linii citite
    if len(lines) < 8:
        raise ValueError("Fișierul nu conține suficiente linii. Verifică formatul fișierului.")

    # Extrage datele din fișier
    d = int(lines[7].split('=')[1].strip().strip(';'))
    r = int(lines[8].split('=')[1].strip().strip(';'))
    SCj = np.array(eval(lines[10].split('=')[1].strip().strip(';').replace(' ', ',')))
    Fj = np.array(eval(lines[11].split('=')[1].strip().strip(';').replace(' ', ',')))
    Dk = np.array(eval(lines[12].split('=')[1].strip().strip(';').replace(' ', ',')))

    # Citirea matricei Cjk
    matrix_data = ''
    for line in lines:
        if 'Cjk' in line:  # Căutăm linia care conține Cjk
            # Extragem doar valoarea matricei de pe linie
            matrix_data = line.split('=')[1].strip().strip(';')  # Extragem partea cu valorile
            break

    # Acum combinăm toate liniile care conțin matricea
    for line in lines[lines.index(line) + 1:]:
        if line.strip() == '':  # Ignorăm liniile goale
            continue
        if '];' in line:  # Dacă linia conține finalul matricei, oprim
            matrix_data += line.split('];')[0].strip()
            break
        matrix_data += line.strip()  # Adăugăm liniile continuate ale matricei

    # Înlocuim spațiile cu virgule și corectăm parantezele
    matrix_data = matrix_data.replace(' ', ',')  # Înlocuim spațiile cu virgule
    matrix_data = matrix_data.replace('][', '],[')  # Corectăm separarea rândurilor
    matrix_data = f'{matrix_data}]'  # Închid parantezele pentru a forma lista corectă

    print("matrix_data înainte de evaluare:", matrix_data)

    # Evaluăm pentru a transforma într-o matrice validă
    try:
        Cjk = np.array(eval(matrix_data))  # Evaluăm pentru a construi matricea
    except SyntaxError as e:
        print(f"Eroare de sintaxă la evaluarea matricei Cjk: {e}")
        Cjk = []

    print("Cjk reparat:", Cjk)

    return d, r, SCj, Fj, Dk, np.array(Cjk, dtype=float)

# Funcția pentru calcularea penalizărilor
def calculate_penalties(costs):
    penalties = []
    for row in costs:
        # Filtrăm valorile finite (eliminăm inf sau NaN)
        finite_row = row[np.isfinite(row)]
        if len(finite_row) > 1:  # Dacă există cel puțin două valori finite
            sorted_row = np.sort(finite_row)
            penalty = sorted_row[1] - sorted_row[0]
        else:
            penalty = 0  # Dacă nu există destule valori finite, penalizarea este zero
        penalties.append(penalty)
    return penalties


# Funcția principală pentru metoda Vogel
def metoda_vogel(SCj, Dk, Cjk, Fj):
    total_cost = 0
    allocations = np.zeros((len(SCj), len(Dk)))
    iteration = 0

    while np.any(Dk > 0):
        penalties = calculate_penalties(Cjk)
        max_penalty_index = np.argmax(penalties)

        # Determinarea alocării
        if np.min(Cjk[max_penalty_index]) == float('inf'):
            break

        min_cost_index = np.argmin(Cjk[max_penalty_index])
        allocation = min(SCj[max_penalty_index], Dk[min_cost_index])

        allocations[max_penalty_index, min_cost_index] = allocation
        SCj[max_penalty_index] -= allocation
        Dk[min_cost_index] -= allocation

        # Calcularea costului total
        total_cost += allocation * Cjk[max_penalty_index, min_cost_index]

        # Actualizarea costurilor
        if SCj[max_penalty_index] == 0:
            Cjk[max_penalty_index, :] = float('inf')
        if Dk[min_cost_index] == 0:
            Cjk[:, min_cost_index] = float('inf')

        iteration += 1
    # Adăugarea costurilor fixe
    total_cost += np.sum(Fj * (SCj == 0))  # Adaugă costurile fixe pentru depozitele folosite

    return allocations, total_cost, iteration

def scrie_rezultate_in_excel(df_rezultate, fisier_nou):
    # Verifică dacă fișierul există deja
    if os.path.exists(fisier_nou):
        # Dacă fișierul există, adaugă rezultatele la sfârșit fără a adăuga header-ul
        with pd.ExcelWriter(fisier_nou, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            # Citim datele existente și le combinăm cu cele noi
            df_existent = pd.read_excel(fisier_nou, sheet_name='Rezultate')
            df_combined = pd.concat([df_existent, df_rezultate], ignore_index=True)

            # Eliminăm coloanele goale sau cu valori NA
            df_combined = df_combined.dropna(axis=1, how='all')

            # Scriem datele combinate
            df_combined.to_excel(writer, sheet_name='Rezultate', index=False)
    else:
        # Dacă fișierul nu există, creează-l și scrie datele
        with pd.ExcelWriter(fisier_nou, engine='openpyxl') as writer:
            df_rezultate.to_excel(writer, sheet_name='Rezultate', index=False)

def rezolva_problema_transport(nume_fisier):
    # Citirea datelor din fișier
    d, r, SCj, Fj, Dk, Cjk = read_data_from_file(nume_fisier)

    # Apelăm metoda Vogel
    start_time = time.time()
    allocations, total_cost, iteration = metoda_vogel(SCj, Dk, Cjk, Fj)
    elapsed_time = time.time() - start_time

    # Afișăm rezultatele
    print(f"Fișierul: {nume_fisier}")
    print(f"Costul total minim: {total_cost}")
    print(f"Numărul de iterații: {iteration}")
    print(f"Timp de execuție: {elapsed_time} secunde")

    # Salvăm rezultatele într-un DataFrame
    date_rezultate = {
        "Nume fișier": [nume_fisier],
        "Cost minim": [total_cost],
        "Număr de iterații": [iteration],
        "Timp execuție (sec)": [elapsed_time],
        "Status": ["solved" if total_cost < float('inf') else "unsolved"],
    }

    df_rezultate = pd.DataFrame(date_rezultate)

    # Numele fișierului unde vor fi salvate rezultatele
    fisier_nou = 'rezultate_transport_fcd.xlsx'

    # Apelăm funcția de salvare a rezultatelor în Excel
    scrie_rezultate_in_excel(df_rezultate, fisier_nou)


# Testează funcția
rezolva_problema_transport("Lab01_FCD_large_25.dat")

