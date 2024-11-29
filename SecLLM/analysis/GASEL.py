import os
import pandas as pd
import shutil
import argparse
from collections import defaultdict

def process_csv(input_csv, base_path, output_dir):
    """
    Legge un file CSV, filtra per detector specifici, sostituisce una parte del percorso 
    nei file_path, e copia i file risultanti in una nuova cartella con nomi modificati.
    Inoltre, crea un nuovo dataset CSV contenente solo le righe per i file copiati.
    La colonna file_path viene aggiornata con il nome del file copiato.
    """
    # Leggi il file CSV
    df = pd.read_csv(input_csv, sep=';')
    
    # Filtra per detector specifici
    filtered_df = df[df['detector'].isin(['scansible', 'glitch', 'slac'])]
    
    # Trova i file_path unici
    unique_paths = filtered_df['file_path'].unique()
    
    # Crea la cartella di destinazione se non esiste
    os.makedirs(output_dir, exist_ok=True)
    
    # Lista per le righe del nuovo dataset
    copied_files_data = []

    # Elabora ogni file_path
    for file_path in unique_paths:
        # Sostituisci la base path
        new_path = file_path.replace('/DATA/repos/clones/', base_path)
        
        # Assicurati che il file esista nella nuova posizione
        if os.path.exists(new_path):
            # Costruisci il nuovo nome del file
            file_name = new_path.replace(base_path, "").replace("/", "_")
            
            # Definisci il percorso del file nella cartella di destinazione
            destination_path = os.path.join(output_dir, file_name)
            
            # Copia il file nella nuova posizione
            shutil.copy(new_path, destination_path)
            print(f"File copiato: {new_path} -> {destination_path}")
            
            # Aggiungi la riga corrispondente al nuovo dataset
            row = filtered_df[filtered_df['file_path'] == file_path].copy()
            row['file_path'] = file_name  # Aggiorna file_path con il nome del file copiato
            copied_files_data.append(row)
        else:
            print(f"File non trovato: {new_path}")

    # Creazione del nuovo dataset con le righe dei file copiati
    if copied_files_data:
        copied_df = pd.concat(copied_files_data)
        filtered_csv_path = os.path.join(output_dir, "filtered_dataset.csv")
        copied_df.to_csv(filtered_csv_path, index=False)
        print(f"Nuovo dataset creato: {filtered_csv_path}")
        calculate_metrics(filtered_csv_path, os.path.join(output_dir, "metrics_dataset.csv"))
    else:
        print("Nessun file copiato, nessun dataset creato.")


def calculate_metrics(dataset_csv, output_csv, keep_unscanned=True):
    """
    Calcola tp, fp, fn, precision, e recall per ogni combinazione di file_path, smell_type e detector.
    Salva i risultati in un nuovo dataset.
    """
    # Leggi il dataset
    df = pd.read_csv(dataset_csv)
    
    # Struttura dati per organizzare smell, detector e campioni
    smell_type_to_detector_to_samples = defaultdict(lambda: defaultdict(set))
    
    # Organizza i dati
    for _, row in df.iterrows():
        file_path = row['file_path']
        smell_type = row['smell_type']
        detector = row['detector']
        true_positive = row['true_positive']
        cluster_name = row.get('cluster_name', None)

        if detector not in ('scansible', 'glitch', 'slac'):
            continue
        if not keep_unscanned and cluster_name == 'NotScannedByUs': # and detector == 'scansible':
            continue

        smell_type_to_detector_to_samples[smell_type][detector].add((file_path, true_positive))

    # Strutture dati per risultati
    results = []

    # Ordina i dati per smell_type, file_path e smell_id
    df_sorted = df.sort_values(by=['smell_type', 'file_path', 'smell_id'])

    # Calcola num_overall_tp per ogni combinazione di smell_type e file_path
    smell_type_to_file_path_to_smell_ids = defaultdict(lambda: defaultdict(set))
    
    for _, row in df_sorted.iterrows():
        smell_type = row['smell_type']
        file_path = row['file_path']
        true_positive = row['true_positive']
        smell_id = row['smell_id']
        
        # Conta solo gli smell_id distinti con true_positive == True
        if str(true_positive) == 'True':
            smell_type_to_file_path_to_smell_ids[smell_type][file_path].add(smell_id)

    print(smell_type_to_file_path_to_smell_ids['AdminByDefault'])

    tot = 0
    for l in smell_type_to_file_path_to_smell_ids['AdminByDefault']:
        tot += len(smell_type_to_file_path_to_smell_ids['AdminByDefault'][l])

    print("=====>", tot)

    results = []
    df['true_positive'] = df['true_positive'].astype(str)

    grouped = df.groupby(['smell_type', 'file_path'])
    detectors = ['scansible', 'glitch', 'slac']
    for (smell_type, file_path), group in grouped:
        num_overall_tp = len(smell_type_to_file_path_to_smell_ids[smell_type][file_path]) if smell_type in smell_type_to_file_path_to_smell_ids and file_path in smell_type_to_file_path_to_smell_ids[smell_type] else 0
        
        for d in detectors:
            tp = 0
            fp = 0
            filtered_df = df[(df['smell_type'] == smell_type) & 
                            (df['file_path'] == file_path) & 
                            (df['detector'] == d)]
            for index, row in filtered_df.iterrows():
                # Calcola il numero di veri positivi (TP), falsi positivi (FP) e falsi negativi (FN) per il detector
                tp += 1 if str(row['true_positive']) == 'True' else 0
                fp += 1 if str(row['true_positive']) == 'False' else 0
            fn = num_overall_tp - tp  # FN = num_overall_tp - TP
            # Aggiungi i risultati
            results.append({
                    'smell_type': smell_type,
                    'file_path': file_path,
                    'detector': d,
                    'true_positive': tp,
                    'num_overall_tp': num_overall_tp,
                    'false_positive': fp,
                    'false_negative': fn
            })

    # Crea un DataFrame con i risultati
    results_df = pd.DataFrame(results)

    # Salva il nuovo dataset
    results_df.to_csv(output_csv, index=False)
    print(f"Dataset con metriche salvato in: {output_csv}")


def main():
    """
    Gestisce gli argomenti da linea di comando e avvia l'elaborazione del file CSV.
    """
    parser = argparse.ArgumentParser(description="Processa un CSV e copia file con nomi modificati.")
    parser.add_argument("input_csv", type=str, help="Percorso al file CSV di input.")
    parser.add_argument("base_path", type=str, help="Nuova base path per i file_path.")
    parser.add_argument("output_dir", type=str, help="Cartella di destinazione per i file copiati.")
    
    args = parser.parse_args()
    
    # Esegui la funzione di elaborazione
    process_csv(args.input_csv, args.base_path, args.output_dir)

if __name__ == "__main__":
    main()



