import random
import time
import numpy as np

# Parametrii generării
num_lists = 1000
min_size = 10000
max_size = 100000

# Generăm 1.000 de liste cu lungimi aleatorii și elemente generate aleator
random.seed(42)  # Pentru reproducibilitate
lists = [random.choices(range(1000000), k=random.randint(min_size, max_size)) for _ in range(num_lists)]

# Algoritmi de sortare
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]  # Corectarea permutării

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]
        R = arr[mid:]
        merge_sort(L)
        merge_sort(R)
        i = j = k = 0
        while i < len(L) and j < len(R):
            if L[i] < R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1
        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1
        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Cronometrare pentru fiecare algoritm
sort_algorithms = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
}

# Rezultatele timpilor
timing_results = {name: [] for name in sort_algorithms.keys()}

# Aplicăm algoritmii pe copii ale listelor (pentru a nu afecta originalele)
for name, sort_func in sort_algorithms.items():
    print(f"Testing {name}...")
    for lst in lists[:10] if name in ["Bubble Sort", "Selection Sort", "Insertion Sort"] else lists:
        lst_copy = lst.copy()
        start_time = time.time()
        if name == "Quick Sort":
            lst_sorted = sort_func(lst_copy)  # Quick Sort returnează lista sortată
        else:
            sort_func(lst_copy)
        elapsed_time = time.time() - start_time
        timing_results[name].append(elapsed_time)  # Stocăm timpul

# Analiza rezultatelor
print("\nRezultate finale (timp mediu pe algoritm):")
for name, times in timing_results.items():
    print(f"{name}: {np.mean(times):.6f} secunde (medie)")

with open("timing_results.txt", "w") as file:
    for name, times in timing_results.items():
        file.write(f"{name}: {np.mean(times):.6f} secunde (medie)\n")
