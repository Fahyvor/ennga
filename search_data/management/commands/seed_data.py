from django.core.management.base import BaseCommand, CommandError
from search_data.models import SearchData
import uuid
import random
from datetime import datetime, timedelta

from utility.utils import DATA_TYPE_CHOICES
from utility.models import Country, GeoPoliticalZone, City,State, Clan,SubClan
from random import choice
from django.utils import timezone
from faker import Faker




class Command(BaseCommand):
    help = "Populates the search data database table"

    
    def handle(self, *args, **options):

        """ Create list of dates from a particular period"""
        min_year=2000
        max_year=datetime.now().year
        start = datetime(min_year, 1, 1, 00, 00, 00)
        years = max_year - min_year+1
        end = start + timedelta(days=365 * years)
        dates = [timezone.make_aware(start + (end - start) * random.random(), timezone.get_current_timezone()) for i in range(30)]
        
        """ Setup Few Categories """
        categories = ["Health", "Technology", "Travel", "Education", "Agriculture"]
        sub_categories = ["Fitness", "Programming", "Cultural", "University", "Vegetables"]

        """ This is used to to set the data_id """
        n = 0
        
        """ Get all objects into a list """
        countries = Country.objects.all()
        geo_political_zones = GeoPoliticalZone.objects.all()
        states = State.objects.all()

        cities = City.objects.all()

        clans = Clan.objects.all()
        subclans = SubClan.objects.all()
        
        fake = Faker()

    
        for _ in range(10):
            n = n + 1 
            data_id = n
            data_type = choice(DATA_TYPE_CHOICES)[0]
            country = choice(countries)
            geo_political_zone = choice(geo_political_zones)
            state = choice(states)
            city = choice(cities)
            clan = choice(clans)
            subclan = choice(subclans)
            original_date_created =choice(dates)
            original_last_updated = choice(dates)
            category = choice(categories)
            sub_category =  choice(sub_categories)
            description = fake.text()
        
            SearchData.objects.create(data_id=data_id,data_type=data_type,country=country,geo_political_zone=geo_political_zone,state=state,city=city,clan=clan,subclan=subclan,category=category,sub_category=sub_category, description=description,original_date_created=original_date_created, original_last_updated=original_last_updated)
        self.stdout.write(
                self.style.SUCCESS('Successfully..')
            )