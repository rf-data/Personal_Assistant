## tools_marvin.py
# import
from typing import Callable, List, Literal 
import marvin


# @marvin.model
# class SOPMetadata(BaseModel):
#     title: str
#     author: str
#     version: str

# -> meta = SOPMetadata(document_text)
# Marvin extrahiert automatisch die Felder.
# Das ist ziemlich elegant.



class MarvinClient:
    agents: List  # dict?
    memories: List  # dict? 
    tasks: List  # dict?
    tools: List  # dict?

    def __init__(self, ctx):
        self.agent_name = ctx.agent_name
        self.data=ctx.data
        self.instructions=ctx.instructions
        # self.agents=ctx.agent
        # self.tools=ctx. 
        self.context=ctx.context

        self.labels = ctx.labels
        self.multi_label = ctx.multi_label
        
        self.target=ctx.target
        self.n_targets = ctx.n_targets
        
        return 
    

    def add_agent(self, agent_config: dict):

        return self.agents.append(
                            marvin.Agent(
                            name=self.agent_name,
                            instructions=self.instructions,
                            tools=self.tools
                                )
                            )
    

    def add_memory(self):
        memo = ""
        return self.memories.append(memo)


    def add_task(self, task_config: dict):
        return self.tasks.append(
                            marvin.Task(
                                instructions=self.instructions,
                                result_type=self.task_result,
                                tools=self.tools # Custom tools
                                # context
                                # memories
                                # cli: bool
                                # depends_on: str | list
                                )
                            )

    
    def add_tool(
            self,
            mode: Literal["add", "create"] = "add",
            fn: Callable|None=None
            ): 
        tool = ""
        return self.tools.append(tool)
    

    def cast(
            self    # ctx
            ): 
        return marvin.cast(
                data=self.data,
                target=self.target,
                instructions=self.instructions,
                agent=self.agents,
                context=self.context
                )
    
    def extract(
            self, # ctx: MarvinContext
            ):
        return marvin.extract(
                data=self.data,
                target=self.target,
                instructions=self.instructions,
                agent=self.agents,
                context=self.context
                )

    def classify(
            self
            ):
        
        return marvin.classify(
                data=self.data,
                labels=self.labels,
                multi_label=self.multi_label,
                instructions=self.instructions,
                agent=self.agents,
                context=self.context
                )

    def run_all_tasks(self): 
        return marvin.run_tasks(self.tasks)
    
    def run_single_task(self)
        
        for task in self.tasks:
            # yield task.run()

        return marvin.run()

# @marvin.fn
def let_marvin_say(
                # context, 
                # agents  
                message: str, # =context.say_message,
                instructions: str, # =context.job,
                agent: list,    # =agents,
                context: dict  # =context.job_context
                ):
    """
    ???
    # return marvin.say(
    #             message=context.say_message,
    #             instructions=context.job,
    #             agent=agents,
    #             context=context.job_context
    #             )
    """
    

@marvin.fn
def let_marvin_summarize(
                # context, 
                # agents  
                data: str, 
                instructions: str, # =context.job,
                agent: list,    # =agents,
                context: dict  # =context.job_context
                ):
    """
    Summarize the text.

    marvin.summarize(
            data=context.summarize_data,
            instructions=context.job,
            agent=agents,
            context=context.job_context
            )
    """

@marvin.fn
def let_marvin_generate(
                # context, 
                # agents  
                target, # data_type
                n: int,  
                instructions: str, # =context.job,
                agent: list,    # =agents,
                context: dict  # =context.job_context
                ):
    """
    
    "generate": marvin.generate(
                target=context.generate_target,
                n=context.n_targets,
                instructions=context.job,
                agent=agents,
                context=context.job_context
                )
    """

## quick one-liner
def let_marvin_run(
            context,
            agents=None,
            tools=None
            # results_as,
            ):
    job = context.job
    results_as = context.results_as

    return marvin.run(
                    instructions=job,
                    # instructions: What you want the AI to do
                    result_type=results_as,
                    # result_type: The expected type of the result (defaults to str)
                    context=context.job_context,     
                    tools=tools,    # : Optional list of functions the AI can use
                    # thread: Optional thread for conversation context
                    agents=agents   # Optional list of agents to use
                    # raise_on_failure: Whether to raise exceptions on failure (defaults to True)
                    # handlers: Optional list of handlers for events
                    )

# -> run_tasks()

## marvin.Memory

"""
weather_memory = marvin.Memory(
    key='weather',
    instructions='''
    Store daily weather information including:
    - Temperature
    - Conditions
    - Location
    Format: 'Location: temp, conditions'
    '''
)

import marvin
from marvin.memory.providers import chroma

provider = chroma.ChromaEphemeralMemory()
# or provider = chroma.ChromaPersistentMemory()
# or provider = chroma.ChromaCloudMemory()

memory = marvin.Memory(
    key='knowledge',
    provider=provider
)
"""

## marvin.summarize
# data: The content to summarize
# instructions: Optional guidance for the summary
# agent: Optional custom agent to use
# thread: Optional thread for conversation context
# context: Optional dict of additional context
"""
import marvin

text = '''
The annual baking competition featured thirty contestants this year, each bringing their 
unique recipes and techniques. The highlight was a three-tiered chocolate cake with 
raspberry filling, which won first place. Second place went to a creative take on 
traditional apple pie, while third place was awarded to an innovative gluten-free 
cheesecake.
'''

summary = marvin.summarize(text)
print(summary)

"""


## marvin.say
# message: The message to add to the thread
# instructions: Optional guidance for the agent’s responses
# agent: Optional custom agent to use
# thread: Optional thread to store conversation history
# context: Optional additional context
"""
import marvin

# Create a thread to store the conversation
thread = marvin.Thread()

# Add a message and get a response
response = marvin.say(
    'My name is Alice',
    thread=thread  # Messages are stored in the thread
)
print(response)

# The agent can now reference previous messages
response = marvin.say(
    'What's my name?',
    thread=thread
)
print(response)
"""

## marvin.generate
# target: The type of data to generate
# n: Number of examples to generate (default: 1)
# instructions: Optional guidance for generation
# agent: Optional custom agent to use
# thread: Optional thread for conversation context
# context: Optional additional context
"""
import marvin

name = marvin.generate(
    str,
    instructions="Generate a fantasy character name"
)
print(name)
"""

## marvin.extract
# data: The input data to extract from (any type)
# target: The type of data to extract (defaults to str)
# instructions: Required when target is str to specify what to extract
# agent: Optional custom agent to use
# thread: Optional thread for conversation context
# context: Optional additional context
"""
import marvin

emails = marvin.extract(
    "Contact us at support@example.com or sales@example.com",
    str,
    instructions="Find email addresses"
)
print(emails)
"""

## marvin-classify
# data: The input data to classify (any type)
# labels: Either a sequence of labels or an Enum class
# multi_label: Whether to return multiple labels (defaults to False)
# instructions: Optional instructions to guide classification
# agent: Optional custom agent to use
# thread: Optional thread for conversation context
# context: Optional additional context
"""
import marvin

sentiment = marvin.classify(
    "This product is amazing!",
    ["positive", "negative", "neutral"]
)
print(sentiment)
"""

## marvin.cast
# data: The input data to convert (any type)
# target: The target type to convert to (defaults to str)
# instructions: Optional instructions to guide the conversion
# agent: Optional custom agent to use
# thread: Optional thread for conversation context
# context: Optional additional context
"""
import marvin

# Convert text to a number
price = marvin.cast("three dollars and fifty cents", float)
print(price)
"""

# # Threads maintain conversation history
# with marvin.Thread() as thread:
#     # Ask multiple related questions
#     marvin.run("What is quantum computing?")
#     marvin.run("How does that relate to classical computing?")
#     marvin.run("What are its practical applications?")

# --> agent.run(instruc)

# @marvin.fn
# def translate_to_french(text: str) -> str:
#     """Translate the text into French."""

# @marvin.fn
# def summarize(article: str) -> str:
#     """Create a concise summary."""


# 2. Marvin

# Hier bin ich deutlich vorsichtiger.

# Was ist Marvin?
# Marvin versucht, GPT wie normale Python-Funktionen aussehen zu lassen.

# Beispiel
# ```
# import marvin

# @marvin.fn
# def summarize(text: str) -> str:
#     """Summarize this text."""

# ```
# Dann kannst du einfach

# summary = summarize(text)

# aufrufen.

# Intern ruft Marvin GPT auf.

# Oder

# class SOP(BaseModel):

#     title: str
#     scope: str

# marvin.cast(
#     text,
#     SOP
# )

# liefert direkt

# SOP(...)
# Das ist ziemlich elegant.

# Es fühlt sich fast an wie

# Python
# ↓
# LLM
# ↓
# Python

# anstatt

# Prompt
# ↓
# JSON
# ↓
# Pydantic
# ↓
# Python

# Warum bin ich trotzdem skeptisch?

# Für kleinere Projekte finde ich Marvin großartig.
# Für dein Projekt sehe ich aber einige Nachteile.

# 1. Zu viel Magie
# Du arbeitest bereits mit
# > Pydantic
# > JSON Schema
# > Typed Models

# Marvin versteckt viele Dinge.

# Bei GMP möchte ich möglichst expliziten Code.

# 2. Debugging
# Du hast in den letzten Wochen viele Parsing-Probleme gelöst.
# Mit Marvin ist manchmal schwieriger zu sehen
# > welcher Prompt erzeugt wurde
# > welche Parameter benutzt wurden
# > welche Response genau zurückkam.

# 3. Reproduzierbarkeit
# Für MLflow möchtest du vermutlich loggen

# Prompt
# ↓
# Model
# ↓
# Temperature
# ↓
# JSON
# ↓
# Output

# Mit Marvin ist das etwas indirekter.

# Wo würde ich Marvin trotzdem einsetzen?
# > Nicht für die SOP-Generierung.
# > Nicht für dein Retrieval.
# > Nicht für dein RAG.

# Sondern eher für kleine Hilfsaufgaben.
# Zum Beispiel

# class DocumentType(Enum):

#     SOP
#     Guideline
#     Policy
#     Regulation

# Dann
# doc_type = marvin.classify(...)

# oder
# class PDFMetadata(BaseModel):

#     title: str
#     language: str
#     document_type: str

# metadata = marvin.cast(text, PDFMetadata)

# Dafür eignet sich Marvin sehr gut.
