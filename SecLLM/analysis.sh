#!/bin/bash

# Check if at least directory and output file parameters are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <directory> <output_file> [smell]"
  exit 1
fi

# Get the directory and output file from the arguments
directory="$1"
output_file="$2"
smell="$3"  # Third argument captured as a single string, spaces included

# Find all the files in the given directory (non-recursive)
files=$(find "$directory" -maxdepth 1 -type f)

# Count total number of files
total_files=$(echo "$files" | wc -l)
current_file=0

# Initialize a flag to handle the first file
first=true

# Record the start time
start_time=$(date +%s)

# Debug: Print the smell parameter
if [ -n "$smell" ]; then
  echo "Smell argument passed: '$smell'"
else
  echo "No smell argument provided."
fi

# Loop through all files
for file in $files; do
  current_file=$((current_file + 1))
  
  # Calculate progress percentage
  progress=$((current_file * 100 / total_files))
  
  # Print progress on the same line
  clear
  echo -ne "Processing file ($current_file/$total_files): $file [Progress: $progress%]\r"
  
  # Build the command
  if $first; then
    poetry run python ./secllm/secllm.py -f "$file" -o "$output_file" ${smell:+--smell "$smell"}
    first=false
  else
    poetry run python ./secllm/secllm.py -f "$file" -o "$output_file" --append ${smell:+--smell "$smell"}
  fi
done

# Move to the next line after the loop ends
echo ""

# Record the end time
end_time=$(date +%s)

# Calculate and display the total execution time
elapsed_time=$((end_time - start_time))
echo "Processing completed in $elapsed_time seconds."


