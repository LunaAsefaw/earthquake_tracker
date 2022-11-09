#Importing libraries

import requests
import json
import pandas as pd
from pandas.io.json import json_normalize
from datetime import date
import numpy as np
import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import geopandas as gpd
import arcgis
from arcgis.gis import GIS
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.features import FeatureLayerCollection



# ArcGIS online credentials 
arc_url = "ARC_URL"
arc_username = "YOUR USERNAME"
arc_password = "YOUR PASSWORD"
arc_file ='YOUR FILE ID'


#requesting API and storing the daily data in dataframe

url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime="
today=str(date.today())
response = requests.get(url+today)
json = response.json()
json
df=pd.json_normalize(json, record_path=['features'])


 # Login to ArcGIS Online Portal
gis = GIS(url=arc_url, username=arc_username, password=arc_password)

#data cleaning will go here: column renames and drops

#seperate geommetry into longtitude, latitude and depth of earth quake
df[['long', 'lat', 'depth']] = df['geometry.coordinates'].astype(str).str.strip(',').astype(str).str.split(',{1,}', expand=True)

df['long']=df['long'].str[1:]
df['depth']=df['depth'].str[:-1]

#make data numeric for caluclations and visualisations
df['lat']= pd.to_numeric(df['lat'])
df['long']= pd.to_numeric(df['long'])
df['depth']= pd.to_numeric(df['depth'])

#convert epoch time to universal date and time
df['time']=  pd.to_datetime(df['properties.time'], unit='ms')

df.rename(columns = {'properties.place':'place', 'properties.alert':'alert', 'properties.magType':'Magnitude Type', 'properties.type':'seismic type', 'properties.mag':'magnitude', 'properties.sig':'significance'
                              }, inplace = True)

df.drop(['properties.updated', 'properties.tz', 'properties.url', 'properties.detail', 'properties.felt', 'properties.cdi', 'properties.mmi', 'properties.status', 'properties.tsunami'], axis=1, inplace=True)


#Now export the cleaned dataset
export_file='earthquake_today.geojson'
gdf = gpd.GeoDataFrame(
    df[['lat', 'long', 'depth', 'type', 'significance', 'place', 'Magnitude Type']], geometry=gpd.points_from_xy(df.long, df.lat))
gdf.to_file(filename=export_file, driver='GeoJSON')




#This is incase one could not find the arc_file id 
my_content = gis.content.search(query="owner:" + gis.users.me.username, 
                                item_type="Feature Layer", 
                                max_items=15)
id1=my_content[0]
id=id1.id
id


#this overwrites the data since the data is updated daily
dataitem = gis.content.get(arc_file)
flayercol = FeatureLayerCollection.fromitem(dataitem)
flayercol.manager.overwrite(export_file)



count= df.shape[0]


#start instantiating app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )


#layout section

df2=df['seismic type']

stype=df2.unique().tolist()


df3=df['Magnitude Type']
mtype=df3.unique().tolist()


app.layout= dbc.Container([
    dbc.Row(
        dbc.Col(html.H1('Daily Earthquakes Dashboard',
                        className= 'text-center',
                        style={'color': 'orangered'}),
                width=12)
    ),

    dbc.Row([
        dbc.Col([html.H4(date.today().strftime('%Y-%m-%d'),
                        style={'background-color': 'orangered', 'color': 'black', 'text-align': 'center', 'height': '80%'})],
                width=6),
        dbc.Col([html.H4('Earthquake count: '+ str(count),
                        style={'background-color': 'orangered', 'color': 'black', 'text-align': 'center', 'height': '80%'})],
                width=6)
        
        
    ]),

    dbc.Row([
        
        dbc.Col([
            dcc.Dropdown(id='colorDpdw', multi=False, value='orrd', style={'border-color': 'orangered', 'background-color': 'black' ,'color': 'black'},
                         options= [{
                             'label': 'Orange-red', 'value': 'orrd'},
                             {'label': 'Blue-red', 'value': 'icefire'},
                             {'label':'Thermal', 'value': 'thermal' }])], width={'size':6}),
                    

        dbc.Col([
            dcc.Dropdown(id='maptype', multi=False, value='Points', style={'border-color': 'orangered', 'background-color': 'black' ,'color': 'black'},
                         options= [{'label': 'Points', 'value': 'Points'},
                                   {'label': 'Heatmap', 'value': 'Heatmap'}])], width={'size':6}),


    ]),  


    dbc.Row([
        
        dbc.Col([
            dcc.Graph(id='mainmap', figure={})
        ]),

    ]),

    dbc.Row([
        
        dbc.Col([
            html.H4('Interactive scatter plot', className= 'text-center')])
    ]),  
    dbc.Row([
        
        dbc.Col([
            html.P('There are three types of recorded seismic events recorded: Earthquakes, quarry and explosions. If a quarry or explosion is experienced, you can filter data to only view earthquakes using the drop down below. The scatter plot shows the magnitude and depth of the earthquakes and shows the level of signficance. The signficance value is determined on a number of factors, including: magnitude, maximum MMI, felt reports, and estimated impact. Larger circles indicate a more significant event.', className= 'text-center')])
    ]),  
   
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='types', multi=False, value='earthquake', style={'border-color': 'orangered', 'background-color': 'black' ,'color': 'black'},
                         options= stype)], width={'size':4, 'offset':4}),

         
 
    ]),
    dbc.Row([
        
        dbc.Col([
            dcc.Graph(id='scatter', figure={})
        ], width=12),

    ]),   
    dbc.Row([
        
        dbc.Col([
            html.H4('Interactive line chart of magnitude by time', className= 'text-center')])
    ]),   
 
    dbc.Row([
        
        dbc.Col([
            dcc.Graph(id='line', figure={})
        ], width=12),

    ]), 


     dbc.Row([
         dbc.Col([
              html.H4('Pie chart Different earthquakes magnitude types experienced today', className= 'text-center')])        
 
 
      ]), 
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='charttype', multi=False, value='piechart', style={'border-color': 'orangered', 'background-color': 'black' ,'color': 'black'},
                         options= [{'label': 'Pie Chart', 'value': 'piechart'},
                                   {'label': 'Funnel', 'value': 'funnel'}])], width={'size':4, 'offset':4}),


    ]),      
    
        
    dbc.Row([
        
        dbc.Col([
            dcc.Graph(id='pie', figure={})
        ], width=12),

    ]),

    dbc.Row([
       dbc.Col([
            html.Label(['Link to find definitions of the different magnitude types shown in the pie chart: ', html.A('link', href='https://www.usgs.gov/programs/earthquake-hazards/magnitude-types')], style={'text-align': 'center'})], width={'size': 4, 'offset':4})        


    ]),     
     dbc.Row([
         dbc.Col([
              html.H4('3D Chart showing the depth by latitude (y) and longitude (y)', className= 'text-center')])        
 
 
      ]), 

    dbc.Row([
        
        dbc.Col([
            dcc.Graph(id='surface', figure={})
        ], width=12),

    ]),

 
], fluid=True)


@app.callback(
    Output('mainmap', 'figure'),
    Input('maptype', 'value'),
    Input('colorDpdw', 'value'))

def update_map(type, scale):
    if type=='Points':
 
      map_fig= px.scatter_geo(df,
                            lat=df.lat,
                            lon=df.long,
                            projection='orthographic',
                            color='magnitude',
                            color_continuous_scale=scale,
                            hover_name='place')
      map_fig.update_traces(marker=dict(size=8))

      map_fig.update_layout(
              title = 'Earthquakes today',
              geo = dict(
                  bgcolor='rgba(0,0,0,0)',
                  showland = True,
                  landcolor = "rgba(0,0,0,0.8)",
                  showocean=True,
                  oceancolor='rgba(0,0,0,0.2)',
                  countrywidth = 0.5,
                  subunitwidth = 0.5
              ),
          )
    

      map_fig.update_layout(height=600,  margin={"r":0,"t":0,"l":0,"b":0})
      map_fig.update_layout(
          template='plotly_dark',
          polar_radialaxis_gridcolor="rgba(0, 0, 0, 0)",
          polar_angularaxis_gridcolor="rgba(0, 0, 0, 0)",
          paper_bgcolor= 'rgba(0, 0, 0, 0)'
          ),
      return map_fig
    elif type=='Heatmap':
   
        heatmap = go.Figure(go.Densitymapbox(lat=df.lat, lon=df.long, z=df['magnitude'],
                                         radius=10, colorscale=scale, opacity=0.8))
        heatmap.update_layout(mapbox_style="carto-darkmatter", mapbox_center_lon=180)
        
        heatmap.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        heatmap.update_layout(
          template='plotly_dark',
          plot_bgcolor= 'rgba(0, 0, 0, 0)',
          paper_bgcolor= 'rgba(0, 0, 0, 0)'
          ),        
        return heatmap

@app.callback(
    Output('scatter', 'figure'),
    Input('types', 'value'))

def update_scatter(stype):
    dff=df[df['seismic type']==stype] 
    scatterfig = px.scatter(dff, x="magnitude", y="depth",
	             color="magnitude",
                 size='significance',
                 hover_name="place", log_x=True, size_max=60)   
    scatterfig.update_layout(
      template='plotly_dark',
      plot_bgcolor= 'rgba(0, 0, 0, 0)',
      paper_bgcolor= 'rgba(0, 0, 0, 0)'
      ),    
    return scatterfig        
         

@app.callback(
    Output('line', 'figure'),
    Input('types', 'value'))

def update_line(stype):
    dff2=df[df['seismic type']==stype] 
    line = px.line(dff2, x="time", y="magnitude")
    line.update_layout(title_text='Magnitude with time', title_x=0.5)
    line.update_traces(line_color='orangered')
    line.update_layout(

      template='plotly_dark',
      plot_bgcolor= 'rgba(0, 0, 0, 0)',
      paper_bgcolor= 'rgba(0, 0, 0, 0)'
      ),    
    line.update_xaxes(rangeslider_visible=True)
    return line
  
@app.callback(
    Output('pie', 'figure'),
    Input('charttype', 'value'))

def update_pie(ctype):
    if ctype=='piechart':

        pie = px.pie(df,  names='Magnitude Type') 
        pie.update_layout(title_text= 'Magnitude of earthquake for different earthquake magnitude types',title_x=0.5)
        pie.update_layout(
          template='plotly_dark',
          plot_bgcolor= 'rgba(0, 0, 0, 0)',
          paper_bgcolor= 'rgba(0, 0, 0, 0)'
          ),        
        return pie
    else:
        mlcount= len(df[df['Magnitude Type']=='ml'])
        mdcount= len(df[df['Magnitude Type']=='md'])
        mbcount= len(df[df['Magnitude Type']=='mb'])
        mwwcount= len(df[df['Magnitude Type']=='mww'])
        mwrcount= len(df[df['Magnitude Type']=='mwr'])

        funnel= go.Figure(go.Funnel( 
            y= ['ml', 'md', 'mb', 'mww', 'mwr'],
            x= [mlcount, mdcount, mbcount, mwwcount, mwrcount],
            textposition='inside',
            textinfo= 'value+percent total',
            marker={'color': ['orangered', 'tomato', 'chocolate', 'coral', 'lightsalmon' ]}))
            
       
        funnel.update_layout(
          template='plotly_dark',
          plot_bgcolor= 'rgba(0, 0, 0, 0)',
          paper_bgcolor= 'rgba(0, 0, 0, 0)'
          ),  
        return funnel
    


@app.callback(
    Output('surface', 'figure'),
    Input('colorDpdw', 'value'))

def update_surface(scale):
    
    zf=df[['depth', 'lat', 'long']]

    surface= go.Figure(data=[go.Mesh3d(x=zf['long'], y=zf['lat'], z=zf['depth'], opacity=0.5, color='pink')])
    
    surface.update_layout(
      template='plotly_dark',
      plot_bgcolor= 'rgba(0, 0, 0, 0)',
      paper_bgcolor= 'rgba(0, 0, 0, 0)'
      ),  
    surface.update_layout(height=600,  margin={"r":0,"t":0,"l":0,"b":0})
    return surface


if __name__=='__main__':
    app.run_server(debug=True, port=8050)
