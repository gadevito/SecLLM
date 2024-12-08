from configurator import *


#
# Smell Analyzer
#
class SmellAnalyzer:

    # We need the configurator 
    def __init__(self, configurator):
        self.configurator = configurator

    #
    # Analyze the 'script' to detect the smell 'name' using 'prompt'
    #
    def analyze(self, name, prompt, script, tokens):
        """Checks if a specific smell exists in the given script."""
        # Find the smell configuration based on the name
        smell = self.configurator.getSmellConfig(name)
        
        if not smell:
            raise ValueError(f"Smell with name '{name}' not found in configuration.")
        
        # Now we have the smell details

        severity = smell['severity']
        description = smell['description']

        specificModel = smell['model']
        answerKey = smell['answerKey']
        analysisStart = smell['analysisStart']
        analysisEnd = smell['analysisEnd']
 
        cleaned_text = self.configurator.llm_call(self.configurator.system_prompt, 
                                                          prompt.format(script=script),
                                                          specificModel,
                                                          tokens)

        i = cleaned_text.find(analysisStart)
        analysis = ''

        if i != -1:
            j = cleaned_text.find(analysisEnd)
            s = len(analysisStart)
            analysis = cleaned_text[i+s:j]

        i = cleaned_text.find(answerKey)
        if i !=-1:
            if len(analysis) == 0:
                analysis = cleaned_text[0:i]
            cleaned_text = cleaned_text[i+8:].strip()

            #print("FOUND ANSWER", cleaned_text)
        else:    
            cleaned_text = ""
        res = []
        if len(cleaned_text)>0:
            if cleaned_text.lower().find("none") !=-1:
                return None
            res = cleaned_text.split(", ")
                    
            if len(res) == 1 and cleaned_text.find(",") !=-1:
                res = cleaned_text.split(",")

            for elem in res:
                try:
                    int(elem)
                except ValueError:
                    return None
            return {"smell":name, "lines":res, "description":description, "severity":severity, "analysis":analysis}
        else:
            return None
