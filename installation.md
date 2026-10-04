## Linux / Mac
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_ajaley
python manage.py createsuperuser
python manage.py runserver

## Windows Powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_ajaley
python manage.py createsuperuser
python manage.py runserver
