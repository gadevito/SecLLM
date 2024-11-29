import os
import yaml
import os
from openai import OpenAI
import anthropic

#
# Utility class to store the configuration
#
class Config:
    def __init__(self):
        self._model = "gpt4-o"
        self._MAX_TOKENS = 8192
        self._system_prompt = ""
        self._answerKey = ""
        self._row_format = "#{i + 1} {line}"
        self._smells = []
        self._client = None
        self._tokens = []
        self._scriptTypePrompt = ""
        self._retries = 1

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

    # client Getter and setter 
    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    # tokens Getter and setter
    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, value):
        self._tokens = value

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

        
        self.config.system_prompt= ""
        self.config.answerKey = ""
        self.config.row_format = "#{i + 1} {line}"
        self.config.smells = []
        self.load_smells_config(config)

        self.config.client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
        )

        self.config.clientAnthropic = anthropic.Anthropic(
                # defaults to os.environ.get("ANTHROPIC_API_KEY")
                api_key=os.getenv('ANTHROPIC_API_KEY'),
        )
        self.config.tokens = []
    
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

    def getSmellsByNames(self, names):
        r = []
        for s in self.config.smells:
            if s['name'] in names:
                r.append(s)
                #break
        return r 

    def getSmellNames(self):
        r = []
        for s in self.config.smells:
            r.append(s['name'])
        return r
    
    def getSmellByName(self, name):
        r = []
        for s in self.config.smells:
            if s['name'] == name:
                r.append(s)
                break
        return r

    def getSmellConfig(self, name):
        smell = next((smell for smell in self.config.smells if smell['name'].lower() == name.lower()), None)
        return smell


    def isOpenAIModel(self):
        return self.config.model.startswith("gpt")
    

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

    @property
    def client(self):
        return self.config.client

    @property
    def tokens(self):
        return self.config.tokens

    @property
    def retries(self):
        return self.config.retries
    
if __name__ == '__main__':
    c = Configurator("config.yaml")