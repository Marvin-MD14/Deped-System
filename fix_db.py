# import os
# import django
# from django.db import connection

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# django.setup()

# from documents.models import User

# def create_admin_final():
#     email = "marvindelluza@deped.gov.ph"
#     full_name = "marvindelluza"
#     password = "marvin@123!" # Palitan mo ito kung gusto mo

#     print("Starting Deep Sync and Admin Creation...")
    
#     with connection.cursor() as cursor:
#         # Pilitin nating gawing NULLable lahat ng makulit na columns
#         columns = ['personal_email', 'full_name', 'position', 'contact_number', 'gender', 'address']
#         for col in columns:
#             try:
#                 cursor.execute(f"ALTER TABLE documents_user MODIFY {col} TEXT NULL;")
#             except:
#                 pass

#     # Check kung existing na ang user, kung hindi, gagawa tayo
#     if not User.objects.filter(email=email).exists():
#         User.objects.create_superuser(
#             email=email,
#             full_name=full_name,
#             password=password,
#             personal_email="admin@gmail.com", # Nilagyan na natin para di mag-error
#             address="N/A",
#             position="Super Admin"
#         )
#         print(f"SUCCESS: Superuser '{email}' created successfully!")
#     else:
#         print("Admin already exists.")

# if __name__ == "__main__":
#     create_admin_final()

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from documents.models import School
from documents.choices import SCHOOL_CHOICES

def populate_schools():
    print("--- School Database Population Starting ---")
    
    count = 0
    for code, name in SCHOOL_CHOICES:
        # Pinalitan natin ang 'school_code' ng 'school_id' base sa error mo
        school, created = School.objects.get_or_create(
            school_id=code, 
            defaults={'name': name}
        )
        if created:
            print(f"Success: Added {name}")
            count += 1
        else:
            print(f"Skipped: {name} (Already exists)")

    print(f"--- Finished! {count} new schools added. ---")

if __name__ == "__main__":
    populate_schools()