## sop_prompts.py




SOP_BULLET_PROMPT = f"""
You are a GMP expert.

Eventually, an SOP should be written based on the following query:
{query}

The following chunks were retrieved upon the query. 
Use these chunks to a create a list of bullet points covering 
the most relevant and suitable information:
{retrieved_chunks}

"""



SOP_PROMPT = f"""
You are a GMP expert.

Use the following information:

{bullet_points}

Create a SOP with the structure:

{
md_template
'''Purpose
Scope
Responsibilities
Procedure
References'''
}

If information is missing, write a generic placeholder.
"""
