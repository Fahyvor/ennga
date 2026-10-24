import re
from django.db import migrations
from django.db.models import Q


def update_subclan_node_types(apps, schema_editor):
    SubClan = apps.get_model('utility', 'SubClan')
    road_keywords = [
        'street', ' st.', ' st ', 'road', ' rd.', ' rd ',
        'ave', 'close', ' cls', 'lane', ' ln', 'crescent', 'way', 'dr.', 'drive'
    ]
    q_road = Q()
    for kw in road_keywords:
        q_road |= Q(name__icontains=kw)

    non_roads = SubClan.objects.filter(node_type='STREET').exclude(q_road)
    updated = []
    for sc in non_roads:
        sc.node_type = 'SUB_CLAN'
        if sc.node_id:
            m = re.match(r'^(.*?)/(?:MR/\d+/SR/\d+/STR|STR)[-/]?(\d+)$', sc.node_id)
            if m:
                clan_part, seq = m.group(1), m.group(2)
                sc.node_id = f"{clan_part}/SB/{int(seq):03d}"
        updated.append(sc)

    if updated:
        SubClan.objects.bulk_update(updated, ['node_type', 'node_id'], batch_size=500)


def rollback_subclan_node_types(apps, schema_editor):
    SubClan = apps.get_model('utility', 'SubClan')
    subclans = SubClan.objects.filter(node_type='SUB_CLAN')
    updated = []
    for sc in subclans:
        sc.node_type = 'STREET'
        if sc.node_id:
            m = re.match(r'^(.*?)/SB/(\d+)$', sc.node_id)
            if m:
                clan_part, seq = m.group(1), m.group(2)
                sc.node_id = f"{clan_part}/MR/001/SR/001/STR/{int(seq):03d}"
        updated.append(sc)

    if updated:
        SubClan.objects.bulk_update(updated, ['node_type', 'node_id'], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('utility', '0016_update_street_node_ids'),
    ]

    operations = [
        migrations.RunPython(update_subclan_node_types, rollback_subclan_node_types),
    ]
