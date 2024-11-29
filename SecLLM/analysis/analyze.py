import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import seaborn as sns
import matplotlib.pyplot as plt
import argparse


def load_data(smell_file, oracle_file):
    result = []
    # Load the data from CSV files
    try:
        smell_dataset = pd.read_csv(smell_file, sep=",")  # File with columns PATH, LINE, SMELL
        oracle_dataset = pd.read_csv(oracle_file)  # File with columns PATH, LINE, CATEGORY
        # First iteration
        for _, row in oracle_dataset.iterrows():
            path, line, category = row["PATH"], row["LINE"], row["CATEGORY"]
            match = smell_dataset[(smell_dataset["PATH"] == path) & (smell_dataset["LINE"] == line) & (smell_dataset["SMELL"] == category)]
            
            if not match.empty:
                # add row
                result.append({"PATH": path, "LINE": line, "SMELL": category, "CATEGORY": category})
            elif category != 'none':
                # add a row with SMELL='none'
                result.append({"PATH": path, "LINE": line, "SMELL": "none", "CATEGORY": category})
    except Exception as e:
        smell_dataset = pd.read_csv(smell_file, sep=";")
        oracle_dataset = pd.read_csv(oracle_file)  # File with columns PATH, LINE, CATEGORY
        # First iteration
        for _, row in oracle_dataset.iterrows():
            path, line, category = row["PATH"], row["LINE"], row["CATEGORY"]
            match = smell_dataset[(smell_dataset["PATH"] == path) & (smell_dataset["LINE"] == line) & (smell_dataset["SMELL"] == category)]
            
            if not match.empty:
                # add row
                result.append({"PATH": path, "LINE": line, "SMELL": category, "CATEGORY": category})
            elif category != 'none':
                # add a row with SMELL='none'
                result.append({"PATH": path, "LINE": line, "SMELL": "none", "CATEGORY": category})




    # Seconda iterazione: dal secondo dataset verso il risultato parziale
    for _, row in smell_dataset.iterrows():
        path, line, smell = row["PATH"], row["LINE"], row["SMELL"]
        match = next((r for r in result if r["PATH"] == path and r["LINE"] == line and r["SMELL"] == smell), None)
        
        if not match and smell != 'none':
            # Aggiungi la riga con CATEGORY='none'
            result.append({"PATH": path, "LINE": line, "SMELL": smell, "CATEGORY": "none"})

    # Converte il risultato finale in un DataFrame
    final_result = pd.DataFrame(result)

    # Ordina per leggibilità
    final_result = final_result.sort_values(by=["LINE", "CATEGORY", "SMELL"]).reset_index(drop=True)
    return final_result


def compute_metrics(df_merged):

    # Calcola i falsi positivi e falsi negativi
    FP = len(df_merged[(df_merged['CATEGORY'] == 'none') & (df_merged['SMELL'] != 'none')])
    FN = len(df_merged[(df_merged['CATEGORY'] != 'none') & (df_merged['SMELL'] == 'none')])
    TP  = len(df_merged[(df_merged['CATEGORY'] == df_merged['SMELL']) & (df_merged['SMELL'] != 'none')])
    TN  = len(df_merged[(df_merged['CATEGORY'] == df_merged['SMELL']) & (df_merged['SMELL'] == 'none')])

    print("==========================")
    print(f"False positive: {FP}")
    print(f"False negative: {FN}")
    print(f"True positive: {TP}")
    print(f"True negative: {TN}")
    print("==========================\n")

    # Calculate overall metrics
    accuracy = (TP + TN) / (TP + TN + FP + FN)
    precision = TP / (TP + FP) if (TP + FP) != 0 else 0  # Controlla divisione per zero
    recall = TP / (TP + FN) if (TP + FN) != 0 else 0  # Controlla divisione per zero
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0


    # Display metrics
    print("============== MACRO AVERAGE =============")
    print(f"Accuracy: {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")



def compute_metrics_per_category(df_merged):
    # Compute the confusion matrix
    conf_matrix = confusion_matrix(df_merged['CATEGORY'], df_merged['SMELL'])
    
    # Calculate the metrics for each category
    categories = sorted(df_merged['CATEGORY'].unique())

    print("\n==========================")
    for category in categories:
    # Calcola i falsi positivi e falsi negativi
        if category == 'none':
            filtered_df = df_merged[df_merged['CATEGORY'] == 'none']
            count_series = filtered_df.groupby(['PATH']).size()
            total_count = count_series.sum()
            overall_tp = total_count
            #print("CONTEGGIO VERI NEGATIVI PER NONE", total_count)
        else:
            filtered_df = df_merged[df_merged['CATEGORY'] == category]
            count_series = filtered_df.groupby(['PATH', 'CATEGORY', 'LINE']).size()
            total_count = count_series.sum()
            overall_tp = total_count
            print("CONTEGGIO VERI POSITIVI PER", category, total_count)

        FP = len(df_merged[(df_merged['CATEGORY'] == 'none') & (df_merged['SMELL'] != 'none') & (df_merged['SMELL'] == category)])
        
        #FN = len(df_merged[(df_merged['CATEGORY'] != 'none') & (df_merged['CATEGORY'] == category) & (df_merged['SMELL'] == 'none')])
        TP  = len(df_merged[(df_merged['CATEGORY'] == df_merged['SMELL']) & (df_merged['SMELL'] == category) & (df_merged['SMELL'] != 'none')])
        FN = overall_tp - TP
        TN  = len(df_merged[(df_merged['CATEGORY'] == df_merged['SMELL']) & (df_merged['SMELL'] == 'none')])

        if category == 'none':
            FP = len(df_merged[(df_merged['CATEGORY'] == 'none') & (df_merged['SMELL'] != 'none')])
            TN  = len(df_merged[(df_merged['CATEGORY'] == df_merged['SMELL']) & (df_merged['SMELL'] == 'none')])
            FN = len(df_merged[(df_merged['CATEGORY'] != 'none') & (df_merged['SMELL'] == 'none')])
            TP = TN

        # Compute metrics for each category
        accuracy = (TP + TN) / (TP + TN + FP + FN)
        precision = TP / (TP + FP) if (TP + FP) != 0 else 0  # Controlla divisione per zero
        recall = TP / (TP + FN) if (TP + FN) != 0 else 0  # Controlla divisione per zero
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0

        # Display metrics for each category
        print(f"Category: {category}")
        print("--------------------------\n")
        print(f"False positive: {FP}")
        print(f"False negative: {FN}")
        print(f"True positive: {TP}")
        print(f"True negative: {TN}","\n")

        print(f"Accuracy: {accuracy:.2f}")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1 Score: {f1:.2f}")
        print("==========================\n")


    return conf_matrix


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Compute the confusion matrix and metrics for the CSV files.")
    
    # Add arguments for the files
    parser.add_argument("smell_file", help="Path to the file with predicted labels (SMELL).")
    parser.add_argument("category_file", help="Path to the file with true categories (CATEGORY).")
    # Add argument for the output file
    parser.add_argument("--output", help="Path to save the merged CSV file.", default=None)
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Load the data from the provided file paths
    df_merged = load_data(args.smell_file, args.category_file)
    
    # Compute metrics and confusion matrix
    #conf_matrix = compute_metrics(df_merged)
    
    compute_metrics_per_category(df_merged)
    # Calculate and print TP, FP, TN, FN for each category
    categories = sorted(df_merged['CATEGORY'].unique())

    #calculate_tp_fp_tn_fn(conf_matrix, categories)

    # If output path is provided, save the merged DataFrame to CSV
    if args.output:
        df_merged.to_csv(args.output, index=False)
        print(f"Merged data saved to {args.output}")

if __name__ == "__main__":
    main()
