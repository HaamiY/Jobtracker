name: Run Job Tracker

on:
  schedule:
    - cron: '0 0 */2 * *'
  workflow_dispatch:

jobs:
  run-code:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install requests

      - name: Run the script
        env:
          RAPIDAPI_KEY: ${{ secrets.RAPIDAPI_KEY }}
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
          SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
          RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
        run: python auto_job_tracker.py

      - name: Save seen jobs changes
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@://github.com"
          git add seen_jobs.json || true
          git commit -m "Automated update of seen_jobs.json" || echo "No changes to commit"
          git push || true
