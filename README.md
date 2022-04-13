# PACMAN-EUTOPIA
PACMAN capture the flag contest for EUTOPIA partners

To install the packages:
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd pacman-contest
pip install -e .
```

To run a simple example (after installation):
```shell
cd src/
rm -rf upf-ai2* www/
python contest_manager.py
```

The results are accessible from ```src/www/index.html``` file.
