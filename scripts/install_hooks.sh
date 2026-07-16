#!/bin/bash

# Create an install-hooks.sh file in the root of your repository
# $ touch install-hooks.sh

cd .git/hooks
if [ ! -f pre-commit ]; then
    cat << 'EOF' > pre-commit
#!/bin/sh

if git grep --cached -q 'TODO'; then
    echo 'Your commit contains TODO comments. Resolve them before committing.'
    exit 1
fi

EOF
chmod +x pre-commit
fi

##############################
# --> LINTING
# Step 1: Make sure ESLint is installed in your project
# $ npm install eslint --save-dev

# Step 2: Modify the pre-commit hook to include ESLint check
# $ nano .git/hooks/pre-commit

# Add the following code to the pre-commit hook
#!/bin/sh

# ESLINT="$(npm bin)/eslint"

# Run ESLint on staged .js files
# for file in $(git diff --cached --name-only --diff-filter=ACM | grep ".js$"); do
#  if ! $ESLINT "$file"; then
#    echo "ESLint failed on staged file '$file'. Please fix the errors and try again."
#    exit 1
#  fi
# done

##############################
# --> CODE QUALITY by Unit tests

# Assure Jest is installed
# $ npm install jest --save-dev

# Modify the pre-commit hook
# $ nano .git/hooks/pre-commit

# Add the following code:
#!/bin/sh

# JEST="$(npm bin)/jest"

# Running Jest tests
# if ! $JEST; then
#    echo "Tests failed. Fix errors and try committing again."
#    exit 1
# fi
