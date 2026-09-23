from django.core.management.base import BaseCommand
from platform_admin.models import MarketSector
from search_data.models import SearchData


class Command(BaseCommand):
    help = 'Seed data from MarketSector into SearchData'

    def handle(self, *args, **kwargs):
        market_sectors = MarketSector.objects.all()

        for sector in market_sectors:
            SearchData.objects.create(
                data_id=sector.id,
                data_type='market_sector',
                country=sector.country,
                geo_political_zone=sector.geo_political_zone,
                state=sector.state,
                city=sector.city,
                clan=sector.clan,
                subclan=sector.subclan,
                category=sector.category.name if sector.category else None,
                sub_category=sector.sub_category.name if sector.sub_category else None,
                description=sector.description,
                is_deleted=sector.is_deleted,
                original_date_created=sector.date_created,
                original_last_updated=sector.last_updated,
            )
