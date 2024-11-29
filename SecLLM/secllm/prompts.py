SYSTEM_ROLE = """You are an expert of IaC Security. Your are tasked to analyze the script I'll provide."""

USER_SCRIPT_TYPE = """# OBJECTIVE #
Your task is to identify the following script type.

# RESPONSE FORMAT #
Answer after "Script type:" only with Ansible, Puppet, or Chef.
For example:
Script type: Puppet

<iac_script>
{script}
<iac_script>

Script type:"""