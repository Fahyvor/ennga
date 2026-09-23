from django import forms
from .models import MarketSector, MarketSectorBulkData, HistoricalCategory, GeoPhysicalData, MarketSectorCategory, Historical, GeoPhysicalCategory, MarketSectorSubCategory
from utility.models import Country, State, City, Clan, GeoPoliticalZone
from ckeditor_uploader.fields import RichTextUploadingFormField


class MarketSectorBulkDataForm(forms.ModelForm):
    state = forms.ModelChoiceField(
            label='State Location',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=State.objects.all(),
        )


    city = forms.ModelChoiceField(
            label='City',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=City.objects.all(),
        )
    class Meta:
        model = MarketSectorBulkData
        fields = ('filez', 'state', 'city')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.none()

        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['city'].queryset = self.instance.state.city_set.order_by('name')


class MarketSectorForm(forms.ModelForm):
    state = forms.ModelChoiceField(
            label='State Location',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=State.objects.all(),
        )


    city = forms.ModelChoiceField(
            label='City',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=City.objects.all(),
        )

    clan = forms.ModelChoiceField(
            label='Clan',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=Clan.objects.all(),
        )

    geo_political_zone = forms.ModelChoiceField(
            label='Geo Political Zone',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPoliticalZone.objects.all(),
        )

    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorCategory.objects.all(),
        )

    sub_category = forms.ModelChoiceField(
            label='Market Sector Sub Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorSubCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = MarketSector
        fields = ['state', 'city',
                    'clan', 'geo_political_zone', 'category', 'sub_category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].queryset = State.objects.none()
        self.fields['city'].queryset = City.objects.none()
        self.fields['clan'].queryset = Clan.objects.none()
        self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.none()

        self.fields['state'].required = False
        self.fields['city'].required = False
        self.fields['clan'].required = False
        self.fields['geo_political_zone'].required = False
        self.fields['category'].required = False
        self.fields['sub_category'].required = False

        if 'geo_political_zone' in self.data:
            try:
                geo_political_zone_id = int(self.data.get('geo_political_zone'))
                self.fields['state'].queryset = State.objects.filter(geo_political_zone_id=geo_political_zone_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty state queryset
        elif self.instance.pk:
            self.fields['state'].queryset = self.instance.geo_political_zone.state_set.order_by('name')

        # if 'state' in self.data:
        #     try:
        #         state_id = int(self.data.get('state'))
        #         self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
        #     except (ValueError, TypeError):
        #         pass  # invalid input from the client; ignore and fallback to empty City queryset
        # elif self.instance.pk:
        #     self.fields['city'].queryset = self.instance.state.city_set.order_by('name')

        # if 'city' in self.data:
        #     try:
        #         city_id = int(self.data.get('city'))
        #         self.fields['clan'].queryset = Clan.objects.filter(city_id=city_id).order_by('name')
        #     except (ValueError, TypeError):
        #         pass  # invalid input from the client; ignore and fallback to empty City queryset
        # # elif self.instance.pk:
        # #     self.fields['clan'].queryset = self.instance.city.clan_set.order_by('name')

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            # self.fields['sub_category'].queryset = self.instance.category.sub_category.order_by('name')
            self.fields['sub_category'].queryset = self.instance.category.marketsectorsubcategory_set.order_by('name')


class MarketSectorGeoPoliticalZoneForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorCategory.objects.all(),
        )

    sub_category = forms.ModelChoiceField(
            label='Market Sector Sub Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorSubCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = MarketSector
        fields = ['category', 'sub_category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            # self.fields['sub_category'].queryset = self.instance.category.sub_category.order_by('name')
            self.fields['sub_category'].queryset = self.instance.category.marketsectorsubcategory_set.order_by('name')


class MarketSectorStateForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorCategory.objects.all(),
        )

    sub_category = forms.ModelChoiceField(
            label='Market Sector Sub Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorSubCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = MarketSector
        fields = ['category', 'sub_category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            # self.fields['sub_category'].queryset = self.instance.category.sub_category.order_by('name')
            self.fields['sub_category'].queryset = self.instance.category.marketsectorsubcategory_set.order_by('name')


class MarketSectorCityForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorCategory.objects.all(),
        )

    sub_category = forms.ModelChoiceField(
            label='Market Sector Sub Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorSubCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = MarketSector
        fields = ['category', 'sub_category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            # self.fields['sub_category'].queryset = self.instance.category.sub_category.order_by('name')
            self.fields['sub_category'].queryset = self.instance.category.marketsectorsubcategory_set.order_by('name')


class MarketSectorClanForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorCategory.objects.all(),
        )

    sub_category = forms.ModelChoiceField(
            label='Market Sector Sub Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=MarketSectorSubCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = MarketSector
        fields = ['category', 'sub_category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = MarketSectorSubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            # self.fields['sub_category'].queryset = self.instance.category.sub_category.order_by('name')
            self.fields['sub_category'].queryset = self.instance.category.marketsectorsubcategory_set.order_by('name')



class HistoricalForm(forms.ModelForm):
    state = forms.ModelChoiceField(
            label='State Location',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=State.objects.all(),
        )


    city = forms.ModelChoiceField(
            label='City',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=City.objects.all(),
        )

    clan = forms.ModelChoiceField(
            label='Clan',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=Clan.objects.all(),
        )

    geo_political_zone = forms.ModelChoiceField(
            label='Geo Political Zone',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPoliticalZone.objects.all(),
        )

    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=HistoricalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = Historical
        fields = ['geo_political_zone', 'state', 'city', 'clan', 'category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].queryset = State.objects.none()
        self.fields['city'].queryset = City.objects.none()
        self.fields['clan'].queryset = Clan.objects.none()

        self.fields['geo_political_zone'].required = False
        self.fields['state'].required = False
        self.fields['city'].required = False
        self.fields['clan'].required = False
        self.fields['category'].required = False
        self.fields['description'].required = False



        

class HistoricalGeoPoliticalZoneForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Historical Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=HistoricalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = Historical
        fields = ['geo_political_zone', 'category', 'description']


class HistoricalStateForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Historical Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=HistoricalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = Historical
        fields = ['category', 'description']


class HistoricalCityForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Historical Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=HistoricalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = Historical
        fields = ['category', 'description']


class HistoricalClanForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Historical Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=HistoricalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)
    

    class Meta:
        model = Historical
        fields = ['category', 'description']



class GeoPhysicalForm(forms.ModelForm):
    state = forms.ModelChoiceField(
            label='State Location',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=State.objects.all(),
        )


    city = forms.ModelChoiceField(
            label='City',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=City.objects.all(),
        )

    clan = forms.ModelChoiceField(
            label='Clan',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=Clan.objects.all(),
        )

    geo_political_zone = forms.ModelChoiceField(
            label='Geo Political Zone',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPoliticalZone.objects.all(),
        )

    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPhysicalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = GeoPhysicalData
        fields = ['geo_political_zone', 'state', 'city', 'clan', 'category', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].queryset = State.objects.none()
        self.fields['city'].queryset = City.objects.none()
        self.fields['clan'].queryset = Clan.objects.none()

        if 'geo_political_zone' in self.data:
            try:
                geo_political_zone_id = int(self.data.get('geo_political_zone'))
                self.fields['state'].queryset = State.objects.filter(geo_political_zone_id=geo_political_zone_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty state queryset
        elif self.instance.pk:
            self.fields['state'].queryset = self.instance.geo_political_zone.state_set.order_by('name')

        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['city'].queryset = self.instance.state.city_set.order_by('name')

        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['clan'].queryset = Clan.objects.filter(city_id=city_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['clan'].queryset = self.instance.city.clan_set.order_by('name')

            

class GeoPhysicalGeoPoliticalZoneForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Market Sector Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPhysicalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = GeoPhysicalData
        fields = ['category', 'description']
       

class GeoPhysicalStateForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Geo Physical Data Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPhysicalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = GeoPhysicalData
        fields = ['category', 'description']

            

class GeoPhysicalCityForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Geo Physical Data Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPhysicalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = GeoPhysicalData
        fields = ['category', 'description']

class GeoPhysicalClanForm(forms.ModelForm):
    category = forms.ModelChoiceField(
            label='Geo Physical Data Category',
            widget=forms.Select(attrs={'class': 'form-control'}),
            queryset=GeoPhysicalCategory.objects.all(),
        )
    
    description = RichTextUploadingFormField(required=True,)


    class Meta:
        model = GeoPhysicalData
        fields = ['category', 'description']