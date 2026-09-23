from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer, tokenizer
from .models import SearchData
from django_elasticsearch_dsl.registries import registry


autocomplete_analyzer = analyzer(
    'autocomplete_analyzer',
    tokenizer=tokenizer('trigram', 'ngram', min_gram=1, max_gram=20),
        filter=['lowercase']
    )
@registry.register_document
class SearchDocument(Document):
    id = fields.IntegerField(attr='id')
    title = fields.TextField()
    data_id = fields.IntegerField()
    fielddata = True
    data_type = fields.TextField(analyzer=autocomplete_analyzer)
    country = fields.ObjectField(
        properties={
            "id" : fields.IntegerField(attr="id"),
            "name" : fields.TextField(),
        }
    )
    geo_political_zone = fields.ObjectField(
        properties={
            "id" :fields.IntegerField(attr='id'),
            "name" : fields.TextField(),
        }
    )
    state = fields.ObjectField(
        properties= {
            "id" :fields.IntegerField(attr='id'),
            "name" : fields.TextField(),
        }
    )
    city =  fields.ObjectField(
        properties= {
            "id" :fields.IntegerField(attr='id'),
            "name" : fields.TextField(),
        }
    )
    data_category = fields.ObjectField(
        properties= {
            "id" :fields.IntegerField(attr='id'),
            "name" : fields.TextField(),
            "data_type" : fields.KeywordField()
        }
    )
    
    data_sub_category = fields.ObjectField(
        properties= {
            "id" :fields.IntegerField(attr='id'),
            "name" : fields.TextField(),
            "data_type" : fields.KeywordField() 
        }
    )
    description = fields.TextField(fields={'raw': fields.KeywordField()})

    # videos = fields.ObjectField(
    #     property = {
    #         "id": fields.IntegerField(attr='id'),
    #         "main_video": fields.TextField(),
    #     }
    # )

    class Django(object):
        model = SearchData

    class Index:
        name = 'search_data'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'max_ngram_diff': 20
        }

    def get_queryset(self):
        return (
            super(SearchDocument, self)
            .get_queryset()
            .filter(is_deleted=False)
        )
