#!/bin/bash

conda create -n SoC python=3.13.7 -y
conda activate SoC

pip install -r requirements.txt

echo "Finish setting up the environment"

echo "Creating .env file"
echo "#!/bin/bash\n" > .env

echo "URL=\"https://soc.ee.ntu.edu.tw/www/\"" >> .env
echo "EMAIL=\"\"" >> .env
echo "PASSWORD=\"\"" >> .env

echo "Finish creating .env file, please fill in your email and password"
