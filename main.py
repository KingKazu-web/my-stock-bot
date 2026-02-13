name: Daily Stock Bot

on:
  schedule:
    - cron: '0 14 * * 1-5'
  workflow_dispatch:

jobs:
  # ... rest of the code ...
