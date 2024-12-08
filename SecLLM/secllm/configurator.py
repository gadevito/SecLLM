import os
import yaml
import os
from openai import OpenAI
import anthropic
import time
import traceback

#
# Utility class to store the configuration
#
class Config:
    def __init__(self):
        self._model = "gpt4-o"
        self._url = None
        self._MAX_TOKENS = 8192
        self._system_prompt = ""
        self._answerKey = ""
        self._row_format = "#{i + 1} {line}"
        self._smells = []
        self._tokens = []
        self._scriptTypePrompt = ""
        self._retries = 1
        self._heuristicScriptIdentification = False

    # url Getter and setter 
    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    # heuristicScriptIdentification Getter and setter 
    @property
    def heuristicScriptIdentification(self):
        return self._heuristicScriptIdentification

    @heuristicScriptIdentification.setter
    def heuristicScriptIdentification(self, value):
        self._heuristicScriptIdentification = value

    # scriptTypePrompt Getter and setter 
    @property
    def scriptTypePrompt(self):
        return self._scriptTypePrompt

    @scriptTypePrompt.setter
    def scriptTypePrompt(self, value):
        self._scriptTypePrompt = value

    # model Getter and setter
    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    # MAX_TOKENS Getter and setter
    @property
    def MAX_TOKENS(self):
        return self._MAX_TOKENS

    @MAX_TOKENS.setter
    def MAX_TOKENS(self, value):
        self._MAX_TOKENS = value

    # system_prompt Getter and setter
    @property
    def system_prompt(self):
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value):
        self._system_prompt = value

    # answerKey Getter and setter
    @property
    def answerKey(self):
        return self._answerKey

    @answerKey.setter
    def answerKey(self, value):
        self._answerKey = value

    # row_format Getter and setter 
    @property
    def row_format(self):
        return self._row_format

    @row_format.setter
    def row_format(self, value):
        self._row_format = value

    # smells Getter and setter 
    @property
    def smells(self):
        return self._smells

    @smells.setter
    def smells(self, value):
        self._smells = value

    # tokens Getter and setter
    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, value):
        self._tokens = value

    # retries Getter and setter
    @property
    def retries(self):
        return self._retries

    @retries.setter
    def retries(self, value):
        self._retries = value

#
# Configuration Manager
#
class Configurator:

    def __init__(self, config="config.yaml", max_tokens=8192):
        self.config = Config()

        self.config.model = "gpt4-o"
        
        self.config.MAX_TOKENS = max_tokens

        self.config.heuristicScriptIdentification = False
        self.config.system_prompt= ""
        self.config.answerKey = ""
        self.config.row_format = "#{i + 1} {line}"
        self.config.smells = []
        self.load_smells_config(config)

        self.clients = {}

        self.config.tokens = []
    
    #
    # Return the LLM client given the model name
    #
    def _getClient(self, model:str):
        client = None
        openai_client = False
        # Actually, the most open LLMs used OpenAI client, so the configuration is based on the provided
        # url.
        if model.startswith("gpt"):
            openai_client = True
            m = model + self.config.url if self.config.url else ""
            if m not in self.clients:
                if self.config.url:
                    client = OpenAI(base_url=self.config.url, api_key="not-needed")
                else:
                    client = OpenAI(
                        api_key=os.environ.get("OPENAI_API_KEY"),
                    )
                self.clients[m] = client
            else:
                client = self.clients.get(m)
        else:
            # Antrhopic
            if model not in self.clients:
                client = anthropic.Anthropic(
                    # defaults to os.environ.get("ANTHROPIC_API_KEY")
                    api_key=os.getenv('ANTHROPIC_API_KEY'),
                )
                self.clients[model] = client
            else:
                client = self.clients.get(model)
        return openai_client, client
    
    #
    # Perform the LLM call
    #
    def llm_call(self, system_prompt:str, user_prompt:str, model:str, tokens:list, backoff_factor=1.0) ->str:
        openai_client, client = self._getClient(model)
        for attempt in range(self.retries):
            try:
                cleaned_text = None
                if openai_client:
                    msg = [{"role": "system", "content": system_prompt}]
                    msg.append({"role": "user", "content":  user_prompt})
                    response = client.chat.completions.create(model=model,
                                            messages=msg,
                                            seed=123,
                                            max_tokens=self.MAX_TOKENS,
                                            temperature = 0)
                    cleaned_text = response.choices[0].message.content
                    tokens.append({"input":response.usage.prompt_tokens, "output":response.usage.completion_tokens})
                else:
                    msg =[]
                    msg.append({"role": "user", "content":  user_prompt})
                    response = client.messages.create(
                                            model=model,
                                            max_tokens=self.MAX_TOKENS,
                                            system=system_prompt,
                                            messages=msg,
                                            temperature = 0
                                        )
                    cleaned_text = response.content[0].text
                    tokens.append({"input":response.usage.input_tokens, "output":response.usage.output_tokens})
                return cleaned_text
            except Exception as e:
                print("An error occurred during processing. Saving current progress...")
                print(traceback.format_exc())
                wait = backoff_factor * (2 ** attempt)
                time.sleep(wait)
        raise Exception(f"Max retries exceeded {model}")

    #
    # Load the smell configuration from the YAML file.
    #
    def load_smells_config(self, config_file):
        # Open and read the YAML configuration file
        with open(config_file, 'r') as file:
            config_data = yaml.safe_load(file)
        
        # Extract the list of smells from the YAML data
        self.config.smells = []
        
        conf = config_data.get('config', [])
        for c in conf:
            self.config.model = c.get('model',"gpt4-o")
            if 'maxTokens' in c:
                self.config.MAX_TOKENS = c.get('maxTokens') 
            self.config.row_format = c.get('rowFormat',"#{r} {line}")
            self.config.answerKey = c.get('answerKey',"ANSWER: ")
            self.config.retries = c.get('retries',4)
            self.config.heuristicScriptIdentification = c.get('heuristicScriptIdentification', False)
            self.config.scriptTypePrompt = c.get('scriptTypePrompt','')
            self.config.system_prompt = c.get('systemPrompt',"You are an expert of IaC Security. Your are tasked to analyze the script I'll provide.")
        # Iterate through each smell entry in the YAML file and create a dictionary
        for smell in config_data.get('smells', []):
            self.config.smells.append({
                'name': smell.get('name'),
                'prompt': smell.get('prompt'),
                'severity': smell.get('severity'),
                'description': smell.get('description'),
                'model': smell.get('model', self.model),
                'answerKey': smell.get('answerKey',self.answerKey),
                'analysisStart': smell.get('analysisStart','REASON: '),
                'analysisEnd': smell.get('analysisEnd','VERIFICATION:'),
                'exclude': smell.get('exclude',''),
                'onlyCheckRegExpr': smell.get('onlyCheckRegExpr','No'),
                'prefilterRegEx': smell.get('prefilterRegEx','').strip(),
                'dontAnalyzeRegEx': smell.get('dontAnalyzeRegEx','')
            })
        
        #print(self.model, self.row_format)
        return self.config.smells

    #
    # Return the configured smells given their names
    #
    def getSmellsByNames(self, names):
        r = []
        for s in self.config.smells:
            if s['name'] in names:
                r.append(s)
                #break
        return r 

    #
    # Return the configured smell names
    #
    def getSmellNames(self):
        r = []
        for s in self.config.smells:
            r.append(s['name'])
        return r
    
    """
    def getSmellByName(self, name):
        r = []
        for s in self.config.smells:
            if s['name'] == name:
                r.append(s)
                break
        return r
    """

    #
    # Return the smell config given its name
    #
    def getSmellConfig(self, name):
        smell = next((smell for smell in self.config.smells if smell['name'].lower() == name.lower()), None)
        return smell
    
    """
    Utility getters for properties
    """
    @property
    def scriptTypePrompt(self):
        return self.config.scriptTypePrompt
    

    @property
    def scriptTypePrompt(self):
        return self.config.scriptTypePrompt

    @property
    def model(self):
        return self.config.model
    

    @property
    def MAX_TOKENS(self):
        return self.config.MAX_TOKENS

    @property
    def system_prompt(self):
        return self.config.system_prompt

    @property
    def answerKey(self):
        return self.config.answerKey

    @property
    def row_format(self):
        return self.config.row_format

    @property
    def smells(self):
        return self.config.smells

    #@property
    #def client(self):
    #    return self.config.client

    @property
    def tokens(self):
        return self.config.tokens

    @property
    def retries(self):
        return self.config.retries
    
    @property
    def heuristicScriptIdentification(self):
        return self.config.heuristicScriptIdentification

    @property
    def url(self):
        return self.config.url
    
if __name__ == '__main__':
    c = Configurator("config.yaml")