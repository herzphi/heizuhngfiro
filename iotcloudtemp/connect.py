from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import iot_api_client as iot
import pandas as pd
from datetime import timedelta
import os

# Get environment variables
YOUR_CLIENT_ID = 'LEE2MI2lNlbbZhNs2s1XBPFSXkzZAUhA'
YOUR_CLIENT_SECRET = 'PIJWDrwgLiSYIopGGR1IjVjsgXrhNQ6R55Hy0nFf0ZZTQhAlXDw4vEppX462eKIZ'

#  Read server side environemnt variables
#YOUR_CLIENT_ID = os.getenv('YOUR_CLIENT_ID')
#YOUR_CLIENT_SECRET = os.environ.get('YOUR_CLIENT_SECRET')


def get_token():
    """
        Generate a token to connect to the
        Arduino API.
    """
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


def revive_connection():
    """
        Generate a new token bc generated tokens are only valid for 300s.
    """
    token = get_token()
    client_config = iot.Configuration(host="https://api2.arduino.cc/iot")
    client_config.access_token = token.get("access_token")
    client = iot.ApiClient(client_config)
    client_properties = iot.PropertiesV2Api(client)
    client_things = iot.ThingsV2Api(client)
    return client_things, client_properties


def get_thing_id(client_things, client_properties):
    """
        Get the thing ids and the property information
        client_things: Client from the Arduino API
        client_properties: Client Client from the Arduino API
    """
    things = client_things.things_v2_list()
    thing_ids = []
    for i in range(len(things)):
        if things[i].name in ['Chris code', 'Noel code']:
            thing_ids.append(things[i].id)
    #   Set IDs
    properties = []
    for thing_id in thing_ids:
        properties.append(client_properties.properties_v2_list(thing_id))
    return thing_id, properties


def checkboxes_table(properties):
    """
        Get the data the properties generated.
        properties: List of all properties of the desired things.
        RETURN:
            df_propids (pandas.DataFrame): One column is one sensor/property.
            dict_propid_list (dict): Translation between
            property ids and property name, thing ids and thing name.
    """
    df_propids = pd.DataFrame({
        'name':[d.name for d in properties],
        'id':[d.id for d in properties],
        'thing_name':[d.thing_name for d in properties],
        'thing_id':[d.thing_id for d in properties]
    })
    property_name = ['t_30','t_38','t_32','t_36','t_37','t_35','t_33','t_24','t_20','t_31','t_34','t_22','t_23','t_21']
    property_purpose = ['WW-Zirkulation Rücklauf','WW-Zirkulation Vorlauf','Vorlauf Heizungsgerät',\
        'Heizungsgerät Rücklauf','Vorlauf Wasserspeicher','Rücklauf Wasserspeicher','Küche Eltern',\
            'Vorlauf Fussbodenheizung gesamt','Fussbodenheizung Vorlauf Bad','Heizung Vorlauf im Ölkeller',\
                'Außentemperatur','Fussbodenheizung Vorlauf Wohnraum','Vorlauf Mixer Heizungsseitig','Rücklauf Mixer Heizungsseitig']
    for name, purpose in zip(property_name, property_purpose):
        row = df_propids[df_propids['name']==name].index
        df_propids.loc[row, 'purpose'] = purpose
    #  Make the dictionary
    dict_propid_list = df_propids.drop(['name', 'thing_name', 'thing_id'], axis=1)\
            .rename(columns={'id':'value', 'purpose':'label'})\
                    .to_dict(orient='records')
    return df_propids, dict_propid_list


def get_data(client_properties, df_propids):
    """
        client_properties: Client from the Arduino API
        df_propids (pandas.DataFrame): Contains all property/thing ids/names
        RETURN
        df (pandas.DataFrame): Raw data.
        df_union (pandas.DataFrame): Averaged data.
    """
    df = pd.DataFrame({})
    for tid ,pid in zip(df_propids.thing_id.values, df_propids.id.values):
        data_dict = client_properties.properties_v2_timeseries(tid, pid).data
        times = [el.time for el in data_dict][:900]
        values = [el.value for el in data_dict][:900]
        df['datetime'] = times
        df[pid] = values
        df['date'] = pd.to_datetime(df['datetime']).dt.strftime('%d.%m.%Y')
        df['time'] = pd.to_datetime(df['datetime']).dt.strftime('%H:%M')
        df['hour'] = pd.to_datetime(df['datetime']).dt.hour + pd.to_datetime(df['datetime']).dt.minute/60
        df['hour_rounded'] = round(pd.to_datetime(df['datetime']).dt.hour + pd.to_datetime(df['datetime']).dt.minute/60)

    # Make the averages
    df_mean = df.drop(['datetime', 'date', 'time', 'hour'], axis=1)\
        .groupby('hour_rounded').agg('mean').add_suffix('_mean')
    df_std = df.drop(['datetime', 'date', 'time', 'hour'], axis=1)\
            .groupby('hour_rounded').agg('std').add_suffix('_std')
    df_union = pd.concat([df_mean, df_std], axis=1)
    df_union['hour_rounded'] = df_union.index
    return df, df_union
