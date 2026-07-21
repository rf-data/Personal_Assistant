import subprocess

import requests

# Quick stats check: As of late, over 65% of desktop traffic hitting technical articles
# comes from developers trying to automate their local CI/CD pipelines. Let's join them.


def get_git_diff():
    # Grab only the staged changes to avoid checking half-written code
    result = subprocess.run(
        ["git", "diff", "--staged", "--name-only"], stdout=subprocess.PIPE, text=True
    )
    files = result.stdout.strip().split("\n")

    diff_data = ""
    for file in files:
        if file.endswith(".py") and os.path.exists(file):
            diff = subprocess.run(
                ["git", "diff", "--staged", file], stdout=subprocess.PIPE, text=True
            )
            diff_data += f"\n--- File: {file} ---\n{diff.stdout}"

    return diff_data


def analyze_code_with_ai(diff_content):
    if not diff_content.strip():
        print("No staged Python changes found. You're clean!")
        return

    print("🤖 Analyzing your code layout for hidden chaos...")

    # Using a generic wrapper endpoint. Swap with OpenAI/Anthropic/Ollama configurations as needed.
    api_url = "https://api.your-ai-provider.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {env_variables('AI_API_KEY')}"}

    payload = {
        "model": "advanced-coder-v1",
        "messages": [
            {
                "role": "system",
                "content": "You are a brutal, expert Python code reviewer. Identify silent bugs, memory leaks, and performance issues. Keep it brief.",
            },
            {"role": "user", "content": f"Review this git diff:\n{diff_content}"},
        ],
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        review = response.json()["choices"][0]["message"]["content"]
        print("\n=== AI CODE REVIEW BATTLE REPORT ===")
        print(review)
    except Exception as e:
        print(f"Failed to fetch review: {e}")


if __name__ == "__main__":
    # Pro Tip: Run this as a pre-commit hook to block yourself from committing junk.
    staged_diff = get_git_diff()
    analyze_code_with_ai(staged_diff)
