import re
from django.db import migrations


def update_street_node_ids(apps, schema_editor):
    SubClan = apps.get_model('utility', 'SubClan')
    streets = SubClan.objects.filter(node_type='STREET')
    updated = []
    for s in streets:
        if s.node_id and '/STR' in s.node_id and '/MR/' not in s.node_id:
            m = re.match(r'^(.*?)/STR[-/]?(\d+)$', s.node_id)
            if m:
                clan_part, seq = m.group(1), m.group(2)
                s.node_id = f"{clan_part}/MR/001/SR/001/STR/{int(seq):03d}"
                updated.append(s)
    if updated:
        SubClan.objects.bulk_update(updated, ['node_id'], batch_size=500)


def rollback_street_node_ids(apps, schema_editor):
    SubClan = apps.get_model('utility', 'SubClan')
    streets = SubClan.objects.filter(node_type='STREET')
    updated = []
    for s in streets:
        if s.node_id and '/MR/001/SR/001/STR/' in s.node_id:
            m = re.match(r'^(.*?)/MR/001/SR/001/STR/(\d+)$', s.node_id)
            if m:
                clan_part, seq = m.group(1), m.group(2)
                s.node_id = f"{clan_part}/STR-{int(seq):03d}"
                updated.append(s)
    if updated:
        SubClan.objects.bulk_update(updated, ['node_id'], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('utility', '0015_subclan_road_relation'),
    ]

    operations = [
        migrations.RunPython(update_street_node_ids, rollback_street_node_ids),
    ]
