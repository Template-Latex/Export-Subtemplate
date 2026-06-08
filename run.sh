#!/bin/bash
eval "$(conda shell.zsh hook)"
conda activate base
python main.py > /dev/null 2>&1 &