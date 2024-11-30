from configurator import *
from preprocessor import *
from analyzer import *
import os
from concurrent.futures import ThreadPoolExecutor
import time
import argparse
import csv
import traceback
from rich import print
#
# SecLLM main class. 
#
class SecLLM:

    def __init__(self, config="config.yaml"):
        self.configurator = Configurator(config)
        self.smells = self.configurator.config.smells
        self.preprocessor = ScriptPreprocessor(self.configurator)
        self.analyzer = SmellAnalyzer(self.configurator)
        self.tokens = []
    
    #
    # Force SecLLM to detect only smell names
    #
    def filterSmells(self, names):
        r = self.configurator.getSmellsByNames(names)
        self.smells = r 

    #
    # Load the script and add line numbers
    #  
    def _loadScript(self, file_path):
        """
        This function takes the path of a script file, reads its content, adds a line number
        before each line, and returns the modified script with numbered lines.
        
        :param file_path: Path to the script file.
        :return: A string with line numbers prepended to each line.
        """
        return self.preprocessor._loadScript(file_path)

    #
    # Analyze the script for the given smell
    #
    def checkSmell(self, name, script):
        script_type, script, prompt = self.preprocessor.preprocess(name, script)

        #print(script_type,"\n",script, "\n",prompt )

        if len(script.strip()) == 0:
            return None
        
        return self.analyzer.analyze(name, prompt, script, self.tokens)
    
    def checkSmells(self, file_path):
        """
        This method processes the script file by adding line numbers and then checks 
        all smells concurrently on the processed script.
        
        :param file_path: Path to the script file.
        :return: A list of results from checking all smells.
        """
        self.tokens = []
        # First, process the script to add line numbers
        processed_script = self._loadScript(file_path)

        # Create a list to store future results from the checkSmell method
        results = []

        start_time = time.time()
        # Use ThreadPoolExecutor to utilize multiple threads for I/O-bound tasks
        with ThreadPoolExecutor(max_workers=len(self.smells)) as executor:
            # Submit tasks for each smell to the executor
            futures = {
                executor.submit(self.checkSmell, smell['name'], processed_script): smell['name']
                for smell in self.smells
            }

            # Collect the results as they complete
            for future in futures:
                smell_name = futures[future]
                try:
                    result = future.result()  # Get the result of checkSmell
                    if result is not None:
                        #result['file'] = file_path
                        results.append(result)
                except Exception as e:
                    print(f"Error processing smell '{smell_name}': {e}")
                    stack_trace = traceback.format_exc()
                    print(stack_trace)
                    print("\n\n")
        end_time = time.time()
        # Calculate the execution time
        execution_time = end_time - start_time

        intk = 0
        outtk = 0
        for t in self.tokens:
            intk += t["input"]
            outtk += t["output"]
        return {"file":file_path, "smells":results, "time":execution_time, "input":intk, "output":outtk}


    def processDirectory(self, dir_path):
        """Processes all script files in a given directory concurrently."""
        results = {}
        start = time.time()
        # Use ThreadPoolExecutor to process multiple files concurrently
        with ThreadPoolExecutor(max_workers=min(len(os.listdir(dir_path)), 10)) as executor:
            futures = {
                executor.submit(self.checkSmells, os.path.join(root, file)): os.path.join(root, file)
                for root, dirs, files in os.walk(dir_path)
                for file in files  # Process YAML files
            }

            for future in futures:
                file_path = futures[future]
                try:
                    result = future.result()
                    results[file_path] = result
                except Exception as e:
                    print(f"Error processing file '{file_path}': {e}")
        end = time.time()
        tt = end-start
        print("TOTAL TIME FOR DIR", tt)
        return results

    def writeResultsToCSV(self, results, output_file, append=False):
        """Writes the results to a CSV file."""
        mode = 'a' if append else 'w'
        with open(output_file, mode=mode, newline='') as file:
            writer = csv.writer(file)
            if not append:
                writer.writerow(["PATH", "LINE", "SMELL", "TIME"])

            for file_path, result in results.items():
                # Extract only the filename from the path
                file_name = os.path.basename(file_path)
                
                # If there are no smells found in the file
                if len(result["smells"]) == 0:
                    writer.writerow([file_name, 0, 'none', result["time"]])
                else:
                    # Write each smell found in the file
                    for smell in result["smells"]:
                        for line in smell["lines"]:
                            writer.writerow([file_name, line, smell["smell"], result["time"]])

#
# Print the results
#
def printResults(result, directory=False):
    if not directory:
        res = result.get('smells', [])
        print(f"\nFile: {result['file']}\n")
        print("=" * 40)
        for r in res:
            print(f"Smell: {r['smell']}")
            print(f"Description: {r['description']}")
            print(f"Lines: {', '.join(map(str, r['lines']))}")
            print(f"Analysis:\n{r['analysis']}")
            print("-" * 40)
        print(f"Time: {result['time']}")
        print(f"Input Tokens: {result['input']}")
        print(f"Output Tokens: {result['output']}\n")
        print("=" * 40)
    else:
        for rx in result.keys():
            r = result[rx]
            #print(r)
            res = r.get('smells', [])
            print(f"\nFile: {r['file']}\n")
            print("=" * 40)
            for r in res:
                print(f"Smell: {r['smell']}")
                print(f"Description: {r['description']}")
                print(f"Lines: {', '.join(map(str, r['lines']))}")
                print(f"Analysis:\n{r['analysis']}")
                print("-" * 40)
            print(f"Time: {r['time']}")
            print(f"Input Tokens: {r['input']}")
            print(f"Output Tokens: {r['output']}\n")
            print("=" * 40)

def main():

    parser = argparse.ArgumentParser(description="Process script files for security smells.")
    parser.add_argument("-c", "--config", help="Path to the configuration file", default="config.yaml")
    parser.add_argument("-f", "--file", help="Path to a single file to check")
    parser.add_argument("-d", "--directory", help="Path to the directory of files to check")
    parser.add_argument("-o", "--output", help="Output CSV file for results")
    parser.add_argument("-a", "--append", action="store_true", help="Append to the output file instead of overwriting")
    parser.add_argument("-s", "--smell", help="Specific smell to check")

    args = parser.parse_args()

    # Initialize SecLLM object
    checker = SecLLM(config=args.config)

    if args.smell:
        checker.filterSmells([args.smell])

    if args.file:
        # Process a single file
        result = checker.checkSmells(args.file)
        
        if args.output:
            checker.writeResultsToCSV({args.file: result}, args.output, append=args.append)
        else:
            printResults(result)
    elif args.directory:
        # Process all files in a directory
        start_time = time.time()
        result = checker.processDirectory(args.directory)
        end_time = time.time()
        print("TOTAL TIME", end_time-start_time)
        if args.output:
            checker.writeResultsToCSV(result, args.output, append=args.append)
        else:
            printResults(result, True)
    else:
        print("Please provide either a file (-f) or a directory (-d) to process.")

if __name__ == '__main__':
    main()