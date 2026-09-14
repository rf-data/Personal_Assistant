# Comparing two obejcts deeply --> what + where + how sth. change?
"""
from deepdiff import DeepDiff
diff = DeepDiff(old_state, new_state)
print(diff)
"""

# Use shell commands in python w/o subpropcess()
"""
import sh
# Run standard shell commands directly
print(sh.ls("-la"))

# Check git status natively
print(sh.git.status())

# Chain commands together effortlessly
print(sh.wc(sh.ls("-1"), "-l"))
"""

# Replacing words in text; faster than regex
"""
from flashtext import KeywordProcessor

processor = KeywordProcessor()
processor.add_keyword("Python", "Python 3")
processor.add_keyword("JS", "JavaScript")

text = "I love coding in Python and JS."
# Replaces all keywords in a single ultra-fast pass
clean_text = processor.replace_keywords(text)
print(clean_text)  # "I love coding in Python 3 and JavaScript."
"""

# FuzzyMatching
"""
from rapidfuzz import process, fuzz

choices = ["PostgreSQL", "SQLite", "MySQL", "MongoDB"]

# Find closest matches to a misspelled query
results = process.extract("postgressql", choices, scorer=fuzz.WRatio, limit=2)
print(results)
# Matches 'PostgreSQL' with a high confidence score
"""

# adding spinners to long-lasting tasks
"""
import time
from yaspin import yaspin

# Displays a live loading animation during long operations
with yaspin(text="Processing heavy pipeline...", color="cyan") as spinner:
    time.sleep(3)  # Simulating heavy work
    spinner.ok("✔ Done!")
"""
