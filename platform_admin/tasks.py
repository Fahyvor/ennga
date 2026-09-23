import csv
from django.core.files.storage import default_storage as storage

from celery import shared_task
from celery.utils.log import get_task_logger

from accounts.models import Profile
# from .models import CustomerCsv, Customer, CustomerStatus
from .models import MarketSector, MarketSectorBulkData


logger = get_task_logger(__name__)


@shared_task
def create_new_customers(newly_saved_form_id, user_profile_id):
    obj = MarketSectorBulkData.objects.get(id=newly_saved_form_id)
    user_profile = Profile.objects.get(id=user_profile_id)

    # Open the just uploaded csv file to enable me get the fields
    with storage.open(obj.filez.name, 'r') as f:
        reader = csv.reader(f, delimiter=',',)
        for i, row in enumerate(reader):
            if row:
                name = row[0]
                address_location = row[1]
                phone_number = row[2]
                description = row[3]

                new_customer = MarketSector.objects.create(
                    user=obj.user,
                    bulk_data=obj,
                    name=name,
                    address_location=address_location,
                    phone_number=phone_number,
                    description=description,
                    country=obj.country,
                    state=obj.state,
                    city=obj.city,
                )

    # Update the CustomerCsv object to True after creating Customers from the csv file
    obj.activated = True
    obj.save()
    return obj