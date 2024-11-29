import traceback
import re

#
# Script preprocessor
#
class ScriptPreprocessor:

    def __init__(self, configurator):
        self.configurator = configurator
    
    #
    # Open the script at file_path and add line numbers.
    #
    def _loadScript(self, file_path):
        """
        This function takes the path of a script file, reads its content, adds a line number
        before each line, and returns the modified script with numbered lines.
        
        :param file_path: Path to the script file.
        :return: A string with line numbers prepended to each line.
        """
        # Open the file and read the content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Add line number before each line
        processed_lines = [self.configurator.row_format.format(r=i+1, line=line).lstrip() for i, line in enumerate(lines)]

        # Join the lines back together into a single string
        processed_script = "".join(processed_lines)

        #print(processed_script)

        return processed_script

    #
    # Filter script lines using the regular expression 'regex'
    #
    def filterBy_regex(self, text, regex):
        """
        Filters the lines of a text that match a given regular expression.
        
        :param text: Input string representing the text to analyze.
        :param regex: Regular expression as a string.
        :return: String with the filtered lines, separated by newline.
        """
        # Compile the regular expression
        pattern = re.compile(regex)
        # Split the text into lines
        lines = text.splitlines()
        # Filter the lines that match the pattern
        filtered_lines = [line for line in lines if pattern.search(line)]
        # Combine the filtered lines into a single string
        return "\n".join(filtered_lines)

    #
    # If the regular expression doesn't have matches, then the script will be no analyzed
    #
    def doNotAnalyze(self, text, regex):
        pattern = re.compile(regex.strip(),re.MULTILINE)

        matches = re.findall(pattern, text)
        if matches:
            return False
        else:
            return True


    #
    # Excludes lines from a text that contain one of the specified URLs considered safe
    #
    def excludeRows(self, text, exclude):
        """
        Excludes lines from a text that contain one of the specified URLs.

        :param text: Input string representing the text to be analyzed.
        :param exclude: Regular expression for the URLs to be excluded.
        :return: String with the excluded lines, separated by newline.
        """
        ex = exclude.split("|")
        #print(ex)
        # Split the text into lines
        lines = text.splitlines()
        filtered_lines = []
        # Keep only the lines that do NOT contain one of the URLs to be excluded
        for r in lines:
            found = False
            for e in ex:
                if r.find(e) != -1:
                    found = True
                    break
            if not found:
                filtered_lines.append(r)
        # Recombine the filtered lines into a single string
        return "\n".join(filtered_lines)

    #
    # Identify the script type using LLM
    #
    def identify_script_type(self, script):
        try:
            if self.configurator.isOpenAIModel():
                msg = [{"role": "system", "content": self.configurator.system_prompt}]
                msg.append({"role": "user", "content":  self.configurator.scriptTypePrompt.format(script=script)})
                response = self.configurator.client.chat.completions.create(model=self.configurator.model,
                                        messages=msg,
                                        seed=123,
                                        max_tokens=self.configurator.MAX_TOKENS,
                                        temperature = 0)
                cleaned_text = response.choices[0].message.content
                self.configurator.tokens.append({"input":response.usage.prompt_tokens, "output":response.usage.completion_tokens})
            else:
                msg =[]
                msg.append({"role": "user", "content":  self.configurator.scriptTypePrompt.format(script=script)})
                response = self.configurator.clientAnthropic.messages.create(
                                        model=self.configurator.model,
                                        max_tokens=self.configurator.MAX_TOKENS,
                                        system=self.configurator.system_prompt,
                                        messages=msg,
                                        temperature = 0
                                    )
                cleaned_text = response.content[0].text

            i = cleaned_text.find("Script type:")
            if i !=-1:
                cleaned_text = cleaned_text[i+12:].strip()
            else:    
                cleaned_text = ""

            return cleaned_text.lower()
        except Exception as e:
            print(f"Failed to process text with LLM: {e}")
            stack_trace = traceback.format_exc()
            print(stack_trace)
            print("\n\n")
    
    #
    # Preprocess the script 'script' for the given smell 'name'
    #
    def preprocess(self, smell_name, script):
        smell = self.configurator.getSmellConfig(smell_name)

        prefilterRegEx = smell['prefilterRegEx']

        doNotAnalyze = smell['dontAnalyzeRegEx']

        #doPrint = False
        if doNotAnalyze and not isinstance(doNotAnalyze,dict):
            if self.doNotAnalyze(script, doNotAnalyze):
                return None, "", ""
            
        if prefilterRegEx:
            if smell['onlyCheckRegExpr'] == 'No':
                script = self.filterBy_regex(script, prefilterRegEx)

                if len(script.strip()) == 0:
                    return None, "", ""
            else:
                scr = self.filterBy_regex(script, prefilterRegEx)
                if len(scr.strip()) == 0:
                    return None, "", ""
                
        exclude = smell['exclude']
        if exclude:
            script = self.excludeRows(script, exclude)
            
        if script == "1. ---" or len(script.strip()) ==0:
            return None, "", ""

        prompt = smell['prompt']
        script_type = None
        if isinstance(prompt, dict):
            script_type = '$unk$'
            # in this case we have multiple prompts specialized in specific script types.
            script_type = self.identify_script_type(script)
            if script_type.lower() in prompt:
                prompt = prompt.get(script_type.lower())
            else:
                prompt = prompt["default"]

        if doNotAnalyze and isinstance(doNotAnalyze,dict):
            if script_type is None:
                script_type = self.identify_script_type(script)

            if script_type.lower() in doNotAnalyze:
                if self.doNotAnalyze(script, doNotAnalyze.get(script_type.lower())):
                    return None, "", ""
                
        return script_type, script, prompt
