set -e

black .
find * -name "*.py" -print | xargs flake8
pytest -vv

echo done
