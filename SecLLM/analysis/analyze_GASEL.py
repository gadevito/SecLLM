import pandas as pd
import sys
import os

# Aggiungi il percorso della cartella secllm al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'secllm'))

from secllm import SecLLM

smell_map = {"Admin by default": "AdminByDefault", 
             "Empty password":"EmptyPassword", 
             "Hard-coded secret": "HardcodedSecret", 
             "Unrestricted IP Address": "UnrestrictedIPAddress", 
             "Use of HTTP without SSL/TLS": "HTTPWithoutSSLTLS", 
             "Use of weak cryptography algorithms":"WeakCryptoAlgorithm", 
             "No integrity check": "MissingIntegrityCheck"  }

def execute_SecLLM(path, dataset, output,singleSmell):
    # Carica il CSV in un DataFrame
    df = pd.read_csv(dataset)
    if not path.endswith(('/', '\\')):
        path += '/'
    

    sec = SecLLM(config="config.yaml")
    if singleSmell is None:
        sec.filterSmells(['Admin by default', 'Empty password', 'Hard-coded secret', 'Unrestricted IP Address', 'Use of HTTP without SSL/TLS', 'Use of weak cryptography algorithms', 'No integrity check'])
    else:
        sec.setSmell(singleSmell)

    smells = sec.getSmellNames()

    res = []
    for smell in smells:
        df_filtered = df[df['smell_type'] == smell_map[smell]]
        # Ordina per file_path
        df_filtered = df_filtered.sort_values(by='file_path', ascending=True)
        #cont = 1

        prev_file ="---"
        for index, row in df_filtered.iterrows():

            #print("FILE============>", cont)

            #cont +=1

            f = row['file_path']
            if prev_file == f:
                continue
            prev_file = f
            
            print(row['file_path'])

            new_filename = path + f
            result = sec.checkSmells(new_filename)

            if len(result["smells"]) == 0:
                continue
            
            location = 1
            for r in result["smells"]:
                print("smell_type", smell)
                print(r["lines"])

                for line in r["lines"]:
                    res.append({"smell_type":smell_map[smell], 
                                "cluster_name": "SecLLMScan", 
                                "sample_id":row['sample_id'],
                                "repo": row['repo'], 
                                "file_path": f,
                                "detector": "secLLM",
                                "location_hint": line,
                                "smell_id": location,
                                "true_positive": "True",
                                "Comment": "" })
                    location +=1

    new_rows_df = pd.DataFrame(res)
    df_extended = pd.concat([df, new_rows_df], ignore_index=True)

    if output:
        df_extended.to_csv(output, sep=';', index=False)

if __name__ == "__main__":
    # Verifica che i parametri siano stati passati correttamente
    if len(sys.argv) < 4:
        print("Uso corretto: python analyze_GASEL.py <path> <dataset.csv> <output.csv>")
        sys.exit(1)

    path = sys.argv[1]    # La path passata come primo argomento
    dataset = sys.argv[2] # Il file CSV passato come secondo argomento
    output = sys.argv[3]
    singleSmell = sys.argv[4] if len(sys.argv) > 4 else None
    # Chiamata alla funzione per generare i nuovi nomi di file
    execute_SecLLM(path, dataset,output,singleSmell)
