from django.shortcuts import render
import requests
from django.core import serializers
from utility.models import SubClan
import json
# Create your views here.

def home(request):
    return render(request, 'public/home.html')


def load_subclans(request):
    # load_subclans_funciton()
    queryset = SubClan.objects.all()
    for subclan in queryset:
        model_data = {
            'country': subclan.country.name,
            'geo_political_zone': subclan.geo_political_zone.name,
            'state': subclan.state.name,
            'city': subclan.city.name,
            'clan': subclan.clan.name,
            'name': subclan.name,
            'is_deleted': subclan.is_deleted,
        }
        print("-------------------")
        print(model_data)


        api_url = "http://127.0.0.1:8001/sub-clan/"
        try:
            # Send the POST request with the provided data
            response = requests.post(api_url, json=model_data)

            # Check if the request was successful (status code 200-299)
            if response.status_code >= 200 and response.status_code < 300:
                # Print the response data (if the server returned any)
                print("Response Data:", response.json())
            else:
                print("Request failed with status code:", response.status_code)

        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)


    return render(request, 'public/home.html')



def load_subclans_funciton():
    # Fetch all data from the SubClan model
    queryset = SubClan.objects.all()

    # Serialize the queryset into JSON format
    serialized_data = serializers.serialize("json", queryset)

    # Parse the JSON data and get key-value pairs for each object
    for entry in serialized_data:
        # Load JSON data for each entry
        data = json.loads(entry)
        print(data)
        
        # # Extract the model fields and their values
        # model_data = data['fields']
        
        # # Print key-value pairs for each field
        # for key, value in model_data.items():
        #     print(f"{key}: {value}")
        
