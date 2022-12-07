from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
#from iotcloudtemp.credentials import YOUR_CLIENT_ID, YOUR_CLIENT_SECRET
import iot_api_client as iot
import pandas as pd
from datetime import timedelta
import os

# Get environment variables
YOUR_CLIENT_ID = os.getenv('YOUR_CLIENT_ID')
YOUR_CLIENT_SECRET = os.environ.get('YOUR_CLIENT_SECRET')


def get_token():
    oauth_client = BackendApplicationClient(client_id=YOUR_CLIENT_ID)
    token_url = "https://api2.arduino.cc/iot/v1/clients/token"

    oauth = OAuth2Session(client=oauth_client)
    token = oauth.fetch_token(
        token_url=token_url,
        client_id=YOUR_CLIENT_ID,
        client_secret=YOUR_CLIENT_SECRET,
        include_client_id=True,
        audience="https://api2.arduino.cc/iot",
    )
    return token


def get_temp_by_hour():
    token = get_token()
    client_config = iot.Configuration(host="https://api2.arduino.cc/iot")
    client_config.access_token = token.get("access_token")
    client = iot.ApiClient(client_config)
    client_properties = iot.PropertiesV2Api(client)
    client_things = iot.ThingsV2Api(client)
    try:
        things = client_things.things_v2_list()
        print('Response positive.')
    except iot.ApiException as e:
        print("An exception occurred: {}".format(e))
    for i in range(len(things)):
        if things[i].name=='DS18B20_Logging_PHILIPP':
            philipp_thing = things[i]
    thing_id = philipp_thing.id
    properties = client_properties.properties_v2_list(thing_id)
    temp0_id = properties[0].id
    to_date_dict = client_properties.properties_v2_timeseries(thing_id, temp0_id)

    data_list = to_date_dict.data
    times, values = ([] for i in range(2))

    for el in data_list:
        times.append(el.time+timedelta(hours=1))
        values.append(el.value)

    df_data = pd.DataFrame({
        'datetime':times,
        'value': values
    })

    df_data['date'] = pd.to_datetime(df_data['datetime']).dt.strftime('%d.%m.%Y')
    df_data['time'] = pd.to_datetime(df_data['datetime']).dt.strftime('%H:%M')
    df_data['hour'] = pd.to_datetime(df_data['datetime']).dt.hour + pd.to_datetime(df_data['datetime']).dt.minute/60
    return df_data


def get_live_temp(client_things, client_properties):
    try:
        things = client_things.things_v2_list()
        for i in range(len(things)):
            if things[i].name=='DS18B20_Logging_PHILIPP':
                philipp_thing = things[i]
        thing_id = philipp_thing.id
        properties_list = client_properties.properties_v2_list(thing_id)
        temp0_id = properties_list[0].id
        properties_data = client_properties.properties_v2_show(thing_id, temp0_id)
        latest_data = properties_data.last_value
        date = properties_data.value_updated_at.date().strftime('%d.%m.')
        time = (properties_data.value_updated_at+timedelta(hours=1)).time().strftime('%H:%M')
        #print('Response positive.')
    except iot.ApiException as e:
        errorlogging = e 
        #print("An exception occurred: {}".format(e))
    return latest_data, date, time


def revive_connection():
    token = get_token()
    client_config = iot.Configuration(host="https://api2.arduino.cc/iot")
    client_config.access_token = token.get("access_token")
    client = iot.ApiClient(client_config)
    client_properties = iot.PropertiesV2Api(client)
    client_things = iot.ThingsV2Api(client)
    return client_things, client_properties