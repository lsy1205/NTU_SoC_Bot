#!/bin/bash

conda create -n SoC python=3.13.7
conda activate SoC

pip install -r requirements.txt

echo "Finish setting up the environment"

echo "ACCOUNT=\"\"" > .env
echo "PASSWORD=\"\"" >> .env

echo "Finish creating .env file, please fill in your account and password"
