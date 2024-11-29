
import pandas as pd
import argparse

def main(filename):
    # Leggi il file CSV
    try:
        df = pd.read_csv(filename,sep=";")
    except Exception as e:
        df = pd.read_csv(filename,sep=",")

    # Raggruppa per 'PATH' e calcola le statistiche desiderate per singoli gruppi
    grouped = df.groupby('PATH')['TIME'].agg(['sum', 'mean', 'median', 'count'])

    # Calcola il numero totale di gruppi
    number_of_groups = grouped.shape[0]

    # Calcola la somma totale e la media totale su tutti i dati
    total_sum = df['TIME'].sum()
    total_mean = df['TIME'].mean()
    total_std = df['TIME'].std()  # Deviazione standard totale su tutti i valori
    total_median = df['TIME'].median()

    # Stampa i risultati
    print(f"Numero totale di gruppi: {number_of_groups}")
    print(f"Somma totale di TIME: {total_sum:.8f}")
    print(f"Media totale di TIME: {total_mean:.8f}")
    print(f"Deviazione standard totale di TIME: {total_std:.8f}")
    print(f"Mediana totale di TIME: {total_median:.8f}")

    # Se vuoi salvare il risultato in un nuovo file CSV
    #output_filename = 'risultato.csv'
    #result.to_csv(output_filename, index=False)
    #print(f"Risultato salvato in {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Processa un file CSV per calcolare la media e la somma di TIME per ciascun PATH.')
    parser.add_argument('filename', type=str, help='Il nome del file CSV da elaborare')

    args = parser.parse_args()
    main(args.filename)
