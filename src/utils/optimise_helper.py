





from time import perf_counter

######################
# PERFORMANCE_ANALYZER
######################

# def benchmark(fn, *args):
#     start = perf_counter()
#     result = fn(*args)
#     elapsed = perf_counter() - start

#     print(f"{fn.__name__}: {elapsed:.6f}s")

#     return result



######################
# DEPENDENCY_ANALYZER
######################

# import ast

# with open("module.py") as f:
#     tree = ast.parse(f.read())

# for node in ast.walk(tree):
#     if isinstance(node, ast.Import):
#         for name in node.names:
#             print(name.name)

######################
# LIST_FUNCTION
######################
# import ast

# def extract_functions(file_path):
#     with open(file_path, "r") as f:
#         tree = ast.parse(f.read())
#     return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

# functions = extract_functions("app.py")
# for fn in functions:
#     print(f"Explain what `{fn}` does and why it exists.")

###################

# with open("app.py", encoding="utf-8") as f:
#     tree = ast.parse(f.read())

# functions = [
#     node.name
#     for node in ast.walk(tree)
#     if isinstance(node, ast.FunctionDef)
# ]

# print(functions)

# ######################
# # RETRY_FRAMEWORK
# ######################

# import time

# def retry(func, attempts=3):
#     for i in range(attempts):
#         try:
#             return func()
#         except Exception:
#             if i == attempts - 1:
#                 raise

#             time.sleep(2 ** i)

# ######################



import ast
import os
'''
def find_unused_imports(path):
    for file in os.listdir(path):
        if file.endswith(".py"):
            tree = ast.parse(open(os.path.join(path, file)).read())
            imports = {n.name for n in ast.walk(tree) if isinstance(n, ast.Import)}
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            unused = imports - names
            if unused:
                print(file, unused)

find_unused_imports("src")
'''

def find_unused_imports(file_path):
    with open(file_path, "r",
              encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    imports = set()
    
    used = set()
    
    for node in ast.walk(tree):
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.Name):
            used.add(node.id)
    return imports - used

# print(find_unused_imports("app.py"))


patterns = {
    "AWS Key":
        r"AKIA[0-9A-Z]{16}",
    "OpenAI Key":
        r"sk-[A-Za-z0-9]{20,}",
    "Generic Token":
        r"(?i)(api|secret|token).{0,20}[=:].+"
}

# limit length of files
# from pathlib import Path

# LIMIT = 500

# for file in Path(".").rglob("*.py"):
#     lines = sum(1 for _ in open(file, encoding="utf-8"))
    
#     if lines > LIMIT:
#         print(f"{file} -> {lines} lines")


# use asynchron functions / concurrency
# import asyncio
# import aiohttp

# urls = [
#     "https://python.org",
#     "https://github.com",
#     "https://pypi.org"
# ]

# async def fetch(session, url):
#     async with session.get(url) as response:
#         print(url, response.status)

# async def main():
#     async with aiohttp.ClientSession() as session:
#         await asyncio.gather(*(fetch(session, u) for u in urls))

# asyncio.run(main())

'''
import traceback

try:
    run_job()
except Exception:
    traceback.print_exc()
'''

# use built-in debugger
# import pdb

# def divide(a, b):
#     pdb.set_trace()
#     return a / b

# divide(20, 5)

# profile a function
# import cProfile

# def slow():
#     return sum(i * i for i in range(5_000_000))

# cProfile.run("slow()")

def scan_file(file_path):
    
    with open(file_path,
              encoding="utf-8",
              errors="ignore") as f:
        content = f.read()
    
    for name, pattern in patterns.items():
        if re.search(pattern, content):
            print(
                f"Potential {name} found "
                f"in {file_path}"
            )

# scan_file("config.py")
