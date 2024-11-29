import pandas as pd
from nltk.metrics.agreement import AnnotationTask
import argparse

def calculate_percent_agreement(ratings):
    total_pairs = 0
    agreement_pairs = 0
    n, k = ratings.shape
    for i in range(n):
        for j in range(k):
            for l in range(j + 1, k):
                total_pairs += 1
                if ratings[i, j] == ratings[i, l]:
                    agreement_pairs += 1
    return agreement_pairs / total_pairs

def load_data(files):
    """
    Load the CSV files containing the annotations (predictions) and combine them into a single DataFrame.
    Each file will contribute its annotations under the same PATH and LINE.
    
    Parameters:
        files (list): List of CSV file paths containing annotations.
    
    Returns:
        DataFrame: Combined DataFrame with annotations from all files.
    """
    dfs = []
    
    for file in files:
        # Read each CSV file
        try:
            df = pd.read_csv(file,sep=";")
        except Exception as e:
            df = pd.read_csv(file,sep=",")

        # Ensure the required columns are present
        df = df[['PATH', 'LINE', 'SMELL']]
        # Add a 'coder' column to identify the source file (annotator)
        df['coder'] = file
        dfs.append(df)
    
    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, axis=0, ignore_index=True)
    
    #print(combined_df)
    return combined_df

def prepare_annotations(df):
    """
    Prepare the data for calculating Fleiss' Kappa.
    Group by PATH and LINE, and aggregate the 'SMELL' predictions for each unique combination.
    Handle cases where annotators identify different smells or no smells.
    Create the appropriate tuple format: (coder, item, label).
    
    Parameters:
        df (DataFrame): DataFrame containing the annotations with 'PATH', 'LINE', 'SMELL', and 'coder'.
    
    Returns:
        list: List of tuples in the format (coder, item, label).
    """
    annotations = []
    
    # Get all unique combinations of PATH and LINE
    all_items = df.groupby(['PATH', 'LINE']).size().reset_index()[['PATH', 'LINE']]
    
    # Ensure all coders are represented for each PATH+LINE combination
    coders = df['coder'].unique()
    
    for _, item in all_items.iterrows():
        path = item['PATH']
        line = item['LINE']
        item_id = f"{path}:{line}"
        
        for coder in coders:
            # Filter data for this coder, PATH, and LINE
            coder_data = df[(df['PATH'] == path) & (df['LINE'] == line) & (df['coder'] == coder)]
            
            if coder_data.empty:
                # If the coder didn't annotate this line, assume no smell
                annotations.append((coder, item_id, 'none'))
            else:
                # Otherwise, add each smell the coder identified
                for _, row in coder_data.iterrows():
                    label = row['SMELL']
                    annotations.append((coder, item_id, label))

    return annotations

def validate_annotations(annotations):
    """
    Validate the annotations to ensure that each item has at least two coders 
    and there is enough variability for calculating Fleiss' Kappa.
    """
    from collections import defaultdict
    
    item_coder_count = defaultdict(set)
    
    for coder, item, label in annotations:
        item_coder_count[item].add(coder)
    
    for item, coders in item_coder_count.items():
        if len(coders) < 2:
            print(f"Warning: Item '{item}' has fewer than 2 coders ({len(coders)} coders).")
    
    print(f"Validation complete: {len(item_coder_count)} unique items checked.")


def calculate_fleiss_kappa(annotations):
    """
    Calculate Fleiss' Kappa score using the provided annotations.
    Each annotation is a tuple (coder, item, label) for each coder's prediction for a given line.
    """
    if len(annotations) == 0:
        print("Error: No valid annotations provided.")
        return None
    
    
    try:
        # Create the AnnotationTask object
        task = AnnotationTask(data=annotations)
        
        # Calculate the Fleiss' Kappa score
        kappa_score = task.multi_kappa()
        return kappa_score
    except Exception as e:
        print(f"Error calculating Fleiss' Kappa: {e}")
        return None

# Valutazione dei risultati
def interpret_fleiss_kappa(kappa):
    if kappa < 0:
        return "Poor agreement"
    elif kappa < 0.20:
        return "Slight agreement"
    elif kappa < 0.40:
        return "Fair agreement"
    elif kappa < 0.60:
        return "Moderate agreement"
    elif kappa < 0.80:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"

def save_to_csv(annotations, output_file):
    """
    Save the formatted annotations to a CSV file.
    
    Parameters:
        annotations (list): List of annotations to save.
        output_file (str): The output file path to save the CSV.
    """
    # Convert the list of annotations to a DataFrame
    df_output = pd.DataFrame(annotations)
    
    # Save to CSV
    df_output.to_csv(output_file, index=False)

def normalize_annotations(df):
    """
    Normalize the annotations into a format where each row contains:
    - PATH
    - LINE
    - LINE_annotator1, LINE_annotator2, ..., LINE_annotatorN
    - SMELL_annotator1, SMELL_annotator2, ..., SMELL_annotatorN
    
    Parameters:
        df (DataFrame): Combined DataFrame containing annotations.
    
    Returns:
        DataFrame: DataFrame in the normalized format, without the extra 'LINE' column.
    """
    # Get all unique combinations of PATH and LINE
    all_items = df.groupby(['PATH', 'LINE']).size().reset_index()[['PATH', 'LINE']]
    
    # Ensure all coders are represented for each PATH+LINE combination
    coders = df['coder'].unique()
    
    # Prepare a list of dictionaries to build the final DataFrame
    normalized_data = []
    
    for _, item in all_items.iterrows():
        path = item['PATH']
        line = item['LINE']
        
        # Initialize the structure for the normalized row
        normalized_row = {'PATH': path}
        
        # For each coder, get their annotation for this (PATH, LINE)
        for idx, coder in enumerate(coders):
            coder_data = df[(df['PATH'] == path) & (df['LINE'] == line) & (df['coder'] == coder)]
            
            if coder_data.empty:
                # If the coder didn't annotate this line, assume 'none'
                normalized_row[f'LINE_ann{idx + 1}'] = 'none'
                normalized_row[f'SMELL_ann{idx + 1}'] = 'none'
            else:
                # Otherwise, use the annotation value
                row = coder_data.iloc[0]
                normalized_row[f'LINE_ann{idx + 1}'] = row['LINE']
                normalized_row[f'SMELL_ann{idx + 1}'] = row['SMELL']
        
        # Append the normalized row to the list
        normalized_data.append(normalized_row)
    
    # Convert the list of dictionaries to a DataFrame
    normalized_df = pd.DataFrame(normalized_data)
    
    return normalized_df


def analyze_smell_agreement(df):
    """
    Analyze agreement for each distinct smell type and identify those with the least agreement.
    """
    smell_agreement = {}

    # Get all unique smells
    unique_smells = df['SMELL'].unique()

    for smell in unique_smells:
        # Filter data for the current smell
        smell_data = df[df['SMELL'] == smell]
        
        # Pivot the data to create a matrix of annotations
        ratings_matrix = smell_data.pivot_table(index=['PATH', 'LINE'], columns='coder', values='SMELL', aggfunc='first').fillna('none').to_numpy()
        
        # Calculate percent agreement for this smell
        percent_agreement = calculate_percent_agreement(ratings_matrix)
        
        # Store the agreement score
        smell_agreement[smell] = percent_agreement
    
    # Sort smells by agreement in ascending order (least agreement first)
    sorted_smells = sorted(smell_agreement.items(), key=lambda x: x[1])
    
    print("Smells with the least agreement:")
    for smell, agreement in sorted_smells:
        print(f"Smell: {smell}, Agreement: {agreement:.4f}")



def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Calculate Fleiss' Kappa score for 5 prediction CSV files.")
    
    # Accept between 2 to 5 CSV files as input
    parser.add_argument('files', nargs='*', help="CSV files containing predictions with columns PATH, LINE, SMELL", type=str)
    parser.add_argument('--output', type=str, help="Output CSV file path to save the results.")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Check that the number of files is between 2 and 5
    if len(args.files) < 2 or len(args.files) > 5:
        print("Please provide between 2 and 5 CSV files.")
        exit(1)
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Load data from the input files
    df = load_data(args.files)
    
    # Prepare annotations for each line from the predictions in the files
    annotations = prepare_annotations(df)
    
    validate_annotations(annotations)

    # Calculate Fleiss' Kappa score
    kappa_score = calculate_fleiss_kappa(annotations)
    
    # Print the result
    print(f"Fleiss' Kappa Score: {kappa_score:.4f}")

    print(interpret_fleiss_kappa(kappa_score))

    if args.output:
        normalized_df = normalize_annotations(df)
        save_to_csv(normalized_df, args.output)
        print(f"Annotations saved to {args.output}")

    # Calculate and print the raw percentage agreement
    ratings_matrix = df.pivot_table(index=['PATH', 'LINE'], columns='coder', values='SMELL', aggfunc='first').fillna('none').to_numpy()
    percent_agreement = calculate_percent_agreement(ratings_matrix)
    print(f"Raw Percentage Agreement: {percent_agreement:.4f}")

    # Analyze and print the smells with the least agreement
    analyze_smell_agreement(df)

if __name__ == "__main__":
    main()
