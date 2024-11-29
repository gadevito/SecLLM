from configurator import *

import time
import traceback

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


        #print(prompt.format(script=script))
        #print("\n")

        retries = self.configurator.retries

        #print(retries)

        tts = 10
        while retries >0:
            try:
                if specificModel.startswith("gpt"):
                    msg = [{"role": "system", "content": self.configurator.system_prompt}]
                    msg.append({"role": "user", "content":  prompt.format(script=script)})
                    response = self.configurator.client.chat.completions.create(model=specificModel,
                                            messages=msg,
                                            seed=123,
                                            max_tokens=self.configurator.MAX_TOKENS,
                                            temperature = 0)
                    cleaned_text = response.choices[0].message.content
                    tokens.append({"input":response.usage.prompt_tokens, "output":response.usage.completion_tokens})
                else:
                    msg =[]
                    msg.append({"role": "user", "content":  prompt.format(script=script)})
                    response = self.configurator.clientAnthropic.messages.create(
                                            model=specificModel,
                                            max_tokens=self.configurator.MAX_TOKENS,
                                            system=self.configurator.system_prompt,
                                            messages=msg,
                                            temperature = 0
                                        )
                    cleaned_text = response.content[0].text
                    tokens.append({"input":response.usage.input_tokens, "output":response.usage.output_tokens})

                #print(cleaned_text)

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


                    #print("RES", res)

                    for elem in res:
                        try:
                            int(elem)
                        except ValueError:
                            return None
                    return {"smell":name, "lines":res, "description":description, "severity":severity, "analysis":analysis}
                else:
                    return None
            except Exception as e:
                print(f"Failed to process text with LLM: {e}", name)
                stack_trace = traceback.format_exc()
                print(stack_trace)
                print("\n\n")
            retries -=1
            time.sleep(tts)
            tts = tts*2

        return None
