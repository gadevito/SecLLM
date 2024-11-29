# SecLLM: Enhancing Security Smell Detection in IaC with Large Language Models
This replication package contains the source code of the prototype implementation of SecLLM, a polyglot security smell detector in IaC scrips.

# **CONTENT**
- * `SecLLM` contains the source code of the tool
- * `glitch-datasets` contains the original GLITCH's oracle datasets
- * `results` contains the results reported in the paper.

# **SETUP**
# Step 1: Download the repository
Download the SecLLM repository and go to the SecLLM directory. 

# Step 2: Install required packages
Here is the command to install required packages:

```
poetry install
```

# **RUN**
To run SecLLM, launch the following command:
```
potry run python ./secLLM/secllm.py -f <script file path>
```
secllm has several switches:
- "-c" or "--config", "Path to the configuration file", default="config.yaml"
- "-f" or "--file", "Path to a single file to check"
- "-d" or "--directory", "Path to the directory of files to check"
- "-o" or "--output", "Output CSV file for results"
- "-a" or "--append", "Append to the output file instead of overwriting"
- "-s" or "--smell", "Specific smell to check"


# **ANALYSIS SCRIPT**

## **SEQUENCIAL ANALYSIS**
To analyze a full path without using the -d flag, you run analysis.sh.
```
Usage: ./analysis.sh <directory> <output_file> [smell]
```

## Precision, recall, and F1-score
To calculate precision, recall, anf f1 scores, launch the analyze.py script:

```
poetry run python ./analysis/analyze.py <output_file> <glitch oracle_dataset.csv> —-output <analysis_output_file>
```

## Feiss Kappa and raw agreement percentage
Prerequisite: execute the SEQUENCIAL ANALYSIS described above, that will create the output.csv file needed to execute the feiss_kappa.py script.

To calculate Feiss Kappa and raw agreement percentage, launch the feiss_kappa.py script:

```
poetry run python ./analysis/feiss_kappa.py <list of output files obtained with the SEQUENCIAL ANALYSIS> --output <output_file>
```
