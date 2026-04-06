#!/bin/bash

echo "Starting Django setup..."

# 1️⃣ Remove migrations folder if exists
# if [ -d "core/migrations" ]; then
#     echo "Removing core/migrations..."
#     rm -rf core/migrations
# fi

# source venv/bin/activate



# 2️⃣ Run migrations
echo "Making migrations..."
python manage.py makemigrations core

echo "Applying migrations..."
python manage.py migrate

# 3️⃣ Import data
echo "Importing JSON..."
python manage.py import_json

echo "Importing courses..."
python manage.py import_courses

# # 4️⃣ Create superuser
# echo "Creating superuser..."
# python manage.py createsuperuser

# # 5️⃣ Run server
# echo "Starting server..."
# python manage.py runserver 0.0.0.0:8000



# chmod +x run.sh
# ./run.sh
# chmod +x run.sh; ./run.sh


# git config --global core.autocrlf false; git add .gitattributes; git add --renormalize  ;git commit -m "Fix line endings"
