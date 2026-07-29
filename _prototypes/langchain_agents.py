# from typing import TypedDict

# from langgraph.graph import StateGraph


# class AgentState(TypedDict):
#     message: str
#     category: str


# def classify(state):
#     text = state["message"]

#     if "invoice" in text.lower():
#         return {"category": "finance"}

#     return {"category": "general"}


# graph = StateGraph(AgentState)

# graph.add_node("classify", classify)

# graph.set_entry_point("classify")

# app = graph.compile()

# result = app.invoke({"message": "Need help with invoice"})

# print(result)

# #####################

# from openai import OpenAI

# client = OpenAI()


# def summarize_email(email_text):
#     response = client.responses.create(
#         model="gpt-5",
#         input=f"""
#         Summarize this email.

#         {email_text}
#         """,
#     )

#     return response.output_text


# ###################

# from langchain.tools import Tool

# research_tool = Tool(
#     name="Research", func=perform_research, description="Research a topic"
# )

# agent.run("Research AI automation tools for agencies")

# #####################

# from langchain.vectorstores import Chroma
# from langchain_openai import OpenAIEmbeddings

# embeddings = OpenAIEmbeddings()

# db = Chroma(persist_directory="./knowledge", embedding_function=embeddings)

# db.add_texts(["Client prefers monthly reports", "Project deadline is August 1"])

# ##################

# SYSTEM = """
# You are an operations assistant.

# Rules:

# 1. Be concise.
# 2. Prioritize actionable items.
# 3. Extract deadlines.
# 4. Identify risks.
# 5. Return markdown.
# """

# response = client.responses.create(model="gpt-5", instructions=SYSTEM, input=email_text)

# ############

# from crewai import Agent

# researcher = Agent(role="Researcher", goal="Gather information")

# writer = Agent(role="Writer", goal="Create report")

# reviewer = Agent(role="Editor", goal="Verify quality")

# ##############
