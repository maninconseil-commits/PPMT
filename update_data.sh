#!/bin/bash
cd ~/PPMT
echo "$(date) - Debut mise a jour PPMT" >> logs/update.log
python3 sources/clean_adzuna.py >> logs/update.log 2>&1
python3 sources/clean_ft.py >> logs/update.log 2>&1
python3 sources/remap_categories.py >> logs/update.log 2>&1
python3 sources/create_db.py >> logs/update.log 2>&1
python3 sources/mapping_adzuna_rome.py >> logs/update.log 2>&1
python3 notebook/ml_tests.py >> logs/update.log 2>&1
echo "$(date) - Fin mise a jour PPMT" >> logs/update.log
