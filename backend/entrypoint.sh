$@

# For some reason this pip install is lost when done within Dockerfile, so it's appended after CMD
pip install -r requirements.txt