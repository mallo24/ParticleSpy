#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import plotly.express as px
import dash
from dash import html,dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ClientsideFunction
import numpy as np
import pandas as pd
from skimage.util import invert
import hyperspy.api as hs
from particlespy.segptcls import process
from skimage.segmentation import mark_boundaries
from particlespy.particle_analysis import parameters
import particlespy.api as ps
from utils import process_image,make_table,make_data
import warnings
warnings.filterwarnings("ignore")
import os
import platform
import plotly.graph_objects as go
app = dash.Dash(external_stylesheets=[dbc.themes.SPACELAB],suppress_callback_exceptions=True, update_title=None)
server = app.server

filename = 'autoSTEM_1.dm4'



tab1=[
        
        dbc.Row([
            dbc.Col([
                html.H5(children='FileName'),
                dcc.Input(id = 'path', style = {'width': '85%', "margin-bottom": "15px"}),
                dbc.Spinner(
                    dcc.Graph(id='display', style={'height': '80vh'}),
                    color="primary"
                )
            ], width={"size": 9}),
            dbc.Col([
                html.Div([
                    html.H5("Pre-filtering Options"),
                    html.P("Rolling Ball Size:"),
                    dcc.Input(id='rolling', value=0, min=0, type="number"),
                    html.P("Gaussian filter kernal Size:"),
                    dcc.Input(id='gaussian', value=0, min=0, type="number"),
                    html.P("Thresholding Options"),
                    dcc.Dropdown(
                    id="Threshold",
                    options=[
                        {'label':'Otsu', 'value':'otsu'},
                        {'label':'Mean', 'value':'mean'},
                        {'label':'Minimum', 'value':'minimum'},
                        {'label':'Yen', 'value':'yen'},
                        {'label':'Isodata', 'value':'isodata'},
                        {'label':'Li', 'value':'li'},
                        {'label':'Local', 'value':'local'},
                        {'label':'Local Otsu', 'value':'local_otsu'},
                        {'label':'Local+ Global Otsu', 'value':'lg_otsu'},
                        {'label':'Niblack', 'value':'niblack'},
                        {'label':'Sauvola', 'value':'sauvola'}
                       
                    ],
                    value="otsu",
                    style={"width": "73%"}
                ),
                html.P("Local filter kernel"),
                dcc.Input(id='local_kernel', value=1, min=1,step=2, type="number"),
                 dcc.Checklist(
                            options=[
                                {"label": "Watershed", "value": "Watershed"},
                            
                            ],
                            value=[],
                            id="checklist-Watershed-options",
                            className="checklist-Watershed",
                ),
                html.P("Watershed Seed Separation"),
                dcc.Input(id='wing_span2', value=0, min=0, type="number", disabled=False),
                html.P("Watershed Seed Erosion"),
                dcc.Input(id='alpha1', value=0, min=0, type="number", disabled=False),
                 dcc.Checklist(
                            options=[
                                {"label": "Invert", "value": "Invert"},

                            ],
                            value=[],
                            id="checklist-Invert-options",
                ),

                html.P("Min Particle Size(px)"),
                dcc.Input(id='MinParticle', value=0, min=0, type="number"),
                    
                 html.P("Display"),
                    dcc.Dropdown(
                    id="image_label",
                    options=[
                        {"label": "Labels","value": "Labels"},
                        {"label": "Image","value": "Image"}
                    ],
                    value="Image",
                    style={"width": "73%"}
                ),                       
                ]),

                html.Hr(),
                html.Div([
                    html.H5("Commands"),
                    dbc.Button("Update", id="display_geometry", color="primary", style={"margin": "5px"},
                               n_clicks_timestamp='0'),
                   
                ]),
                
            ], width=3,style={}),
        ]),
        html.Hr(),
        # dbc.Table(id="tab2_table")
    ]
################################################################################
tab2_labels=['Area', 'Equivalent circular diameter', 'Major axis length', 'Minor axis length', 'Circularity', 'Eccentricity', 'Solidity', 'Total particle intensity', 'Maximum particle intensity', 'X coordinate', 'Y coordinate', 'Bounding box area', 'Bounding box diagonal length']
tab2_values=['area', 'equivalent circular diameter', 'major axis length','minor axis length', 'circularity', 'eccentricity', 'solidity', 'intensity', 'intensity_max', 'x', 'y', 'bbox_area', 'bbox_length']
tab2_options=[{'label': i, 'value': j} for i,j in zip(tab2_labels,tab2_values)]

tab2=[
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Label("No of parameters"),
                    dbc.RadioItems(
                        options=[
                            {"label": "1", "value": 1},
                            {"label": "2", "value": 2},
                        ],
                        value=1,
                        id="no_of_parameters",
                        inline=True,
                    )
                ],width=3),
                dbc.Col([
                    dbc.Label("First Parameter"),
                    dbc.Select(
                        id="tab2_param1",
                        options=tab2_options,
                    )
                ],width=4),
                dbc.Col([
                    dbc.Label("Second Parameter"),
                    dbc.Select(
                        id="tab2_param2",
                        options=tab2_options,
                    )
                ],width=4,
                id="tab2_param2_col"),
                dbc.Col([
                    dbc.Button("Display", color="primary", className="me-1", id="tab2_display", n_clicks_timestamp='0', style={"marginTop": "30px"}),
                ],width=1)
            ])
        ],width=6)
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("All Particles",style={"textAlign":"center",'marginTop':'25px'}),
        ],width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dcc.Graph(id="tab2_scatter_plot", style={"height": "80vh", "width": "100%", "margin": "0"}),
            ]),
        ],width=6),
        dbc.Col([
            dbc.Button('Save Table', id = 'download', className="me-1", color = "primary", style = {'margin-bottom':'20px'}),
            dcc.Download(id = 'download-table'),
            html.Div([dash_table.DataTable(id = 'datatable')],id="tab2_table")
        ],width=5,style={'overflow': 'auto',"height": "85vh", 'margin-bottom': '25px'}),
        
    
    ],justify="evenly"),
]
##############################################################################################

app.layout = dbc.Container(
    [
        dcc.Store(id = 'selected_trace'),
        html.Div(id = 'dummy'),
        dcc.Interval(
            id='interval',
            interval=15000,
            n_intervals=0
        ),
    html.H2("ParticleSpy Dashboard",style={"textAlign":"center","marginTop":"10px"}),
    dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
        dcc.Tab(tab1, label='Segmentation Tab', value='tab-1-example-graph'),
        dcc.Tab(tab2, label='Analysis Tab', value='tab-2-example-graph'),
    ], style = {'margin-bottom': '20px'}),
    html.Div(id='tabs-content-example-graph')],
    fluid=True
)

@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'),
              Input('path', 'value'))
def render_content(tab, path):

    if tab == 'tab-1-example-graph':
        return None

    elif tab == 'tab-2-example-graph':

        if path:
            print('path exists')
            if os.path.isfile(path) == True:
                filenames = [path]
                print('path specifies a file')
            else: 
                print('path is not a file')
                try:
                    print('trying to retrieve the files')
                    files = os.listdir(path)
                    print('files:')
                    print(files)
                    if path[-1] in ['/', "\\"]:
                        filenames = [path + file for file in files]
                        print('path ends with a slash')
                    else:
                        if platform.system == 'Windows':
                            slash = "\\"
                            print('windows')
                        else:
                            slash = '/'
                            print('linux or mac')
                        files = [path + slash + file for file in files]
                        filenames = files
                        # for file in files:
                        #     if file[-4:] == '.dm4':
                        #         filenames.append(file)
                except:
                    filenames = ['autoSTEM_1.dm4']
                
        else:
            filenames = ['autoSTEM_1.dm4']
        dff = pd.DataFrame(columns= ['Waiting for analysis....'])
        dff.to_csv('particles.csv')
        dataframes = []
        #print('created dataframes')
        #print(filenames)
        for file in filenames:
            #print(file)
            data = hs.load(file)
            params = parameters()
            params.load()
            particles = ps.particle_analysis(data, params)
            df=pd.DataFrame(make_data(particles))
            dataframes.append(df)
            df = pd.concat(dataframes)
            df['Particles'] = ['Particle '+str(i) for i in range(1,len(df)+1)]
            df.to_csv("particles.csv",index=False)
        return None
    
@app.callback(
    Output("tab2_param2_col","style"),
    Input("no_of_parameters","value")
)

def change_visibility(no_of_parameters):
    if no_of_parameters==2:
        return {"visibility":"visible"}
    return {"visibility":"hidden"}

@app.callback(
    Output("local_kernel", "disabled"),
    Input("Threshold", "value")
)

def disable_local_kernel(threshold):
    if threshold in ["local", "local_otsu", "lg_otsu", "niblack", "sauvola"]:
        return False
    return True

@app.callback(
    Output("wing_span2", "disabled"),
    Output("alpha1", "disabled"),
    Input('checklist-Watershed-options', 'value')
)

def watershed_options(value):
    if len(value)==0:
        return True,True
    return False,False
#######################################################################################################

# Segmentation parameters and path

@app.callback(
    Output('display', 'figure'),
    Input('display_geometry', 'n_clicks_timestamp'),
    Input('path', 'value'),
    State('rolling', 'value'),
    State('gaussian', 'value'), 
    State('Threshold', 'value'),
    State('local_kernel', 'disabled'),
    State('local_kernel', 'value'),
    State('checklist-Watershed-options', 'value'),
    State('wing_span2', 'value'),
    State('alpha1', 'value'),
    State('checklist-Invert-options', 'value'), 
    State('MinParticle', 'value'),
    State('image_label', 'value'))

def display_geometry(xx,path,roll,gauss,th,local_kernel,local_kernel_value,
                     watershed,wing_span2,alpha1, checklist,min_particle_size,img_label):
    
    if path:
        if os.path.isfile(path) == True:
            filename = path
        else: 
            try:
                files = os.listdir(path)
                if path[-1] in ['/', "\\"]:
                    files = [path + file for file in files]
                else:
                    if platform.system == 'Windows':
                        slash = "\\"
                    else:
                        slash = '/'
                    files = [path + slash + file for file in files]
                    files = [file for file in files if file[-4:] == '.dm4']
                    #print('files2:')
                    #print(files)
            except:
                files = ['autoSTEM_1.dm4']
            filename = files[0]
    else:
        filename = 'autoSTEM_1.dm4'
    
    data = hs.load(filename)
    image = process_image(data)
    
    params = parameters()
    params.generate()
    if xx=='0':
        figure = px.imshow(image, color_continuous_scale='gray')
    else:
        if roll==1:
            params.segment['rb_kernel'] = 0
        else:
            params.segment['rb_kernel'] = roll

        params.segment['gaussian'] = gauss
        params.segment['threshold'] = th

        if local_kernel==False:
            params.segment['local_size'] = local_kernel_value

        if len(watershed)==1:
            params.segment['watershed'] = True
            params.segment['watershed_size'] = wing_span2
            params.segment['watershed_erosion'] = alpha1
        else:
            params.segment['watershed'] = False
        
        params.segment['min_size'] = min_particle_size

       
        params.save()

        labels = process(data,params) # to show the segmented image
        labels = np.uint8(labels*(256/labels.max()))
        if img_label == 'Image':
            b = np.uint8(mark_boundaries(image, labels, color=(1,1,1))[:,:,0]*255)
            if len(checklist)==1:
                figure = px.imshow(invert(b).data, color_continuous_scale='gray')
            else:
                figure = px.imshow(b.data, color_continuous_scale='gray') 

        elif img_label == 'Labels':
           

            figure = px.imshow(labels.data, color_continuous_scale='gray')
            
    figure.update_layout(
        autosize=True,
        yaxis={'visible': False, 'showticklabels': False},
        xaxis={'visible': False, 'showticklabels': False},
        margin=dict(l=0,r=0,b=0,t=0))

    figure.layout.xaxis.fixedrange = True
    figure.layout.yaxis.fixedrange = True
    
    figure.update_traces(hovertemplate=None,hoverinfo='skip')
    figure.update(layout_coloraxis_showscale=False)


    return figure

#############################################################################################
# Tab 2 content:

@app.callback(
    Output("tab2_scatter_plot","figure"),
    Output("tab2_table","children"),
    Input("tab2_display","n_clicks_timestamp"),
    Input('interval', 'n_intervals'),
    Input('datatable', 'active_cell'),
    State("tab2_param1","value"),
    State("tab2_param2","value"),
    State("no_of_parameters","value"),
)

def plot_params(n,interval,active_cell,param1,param2,no_of_parameters):
    df=pd.read_csv("particles.csv")
    df[df.columns[1:]] = df[df.columns[1:]].round(3)
    df = df.rename(columns = {'equivalent circular diameter':'diameter'})
    
    # creating table
    table=dash_table.DataTable(df.to_dict('records'),[{"name": i, "id": i} for i in df.columns if i != "Unnamed: 0"], 
    style_as_list_view=True,  
    style_cell={'overflow': 'hidden','textOverflow': 'ellipsis','Width': "70px",'padding': '15px'},
    style_header={'backgroundColor': 'white','fontWeight': 'bold','border': 'none','border-bottom': '3px solid greys'},
    id = 'datatable')
    
    df=pd.read_csv("particles.csv")
    
    # Histogram
    if (n=='0')|(param1 is None)|('Unnamed: 0' in list(df.columns))|((param2 is None)&(no_of_parameters==2)):
        return px.histogram([i for i in range(0)], nbins= 20, ), table
    
    if no_of_parameters==1:
        fig=px.histogram(df[param1],x=param1, nbins= 20)
        fig.update_layout(title_text='1 property histogram', title_x=0.5)
        
    # Interactive feature
    else:
        if active_cell:
            colors = []
            for i in range(len(df)):
                if i == active_cell['row']:
                    colors.append('red')
                else:
                    colors.append('blue')
            df['color'] = colors
            size = []
            for i in range(len(df)):
                if i == active_cell['row']:
                    size.append(3)
                else:
                    size.append(1)
            df['color'] = colors
            df['size'] = size
            fig = px.scatter(df,x=param1,y=param2, color = 'color', color_discrete_map={'red':'red', 'blue': 'blue'}, size = 'size', size_max=10, hover_data = {'size': False, 'color': False})
            fig.update_layout(showlegend = False)
            
        # Scatterplot    
        else:
            fig = px.scatter(df,x=param1,y=param2, hover_data=['Particles'])
            fig.update_layout(title_text='2 properties plot', title_x=0.5)
    return fig, table
     


# Save the table
@app.callback(
    Output("download-table", "data"),
    Input("download", "n_clicks"),
    prevent_initial_call=True,
)
def download(n_clicks):
    df = pd.read_csv('particles.csv')
    df[df.columns[1:]] = df[df.columns[1:]].round(3)
    df = df.rename(columns = {'equivalent circular diameter':'diameter'})

    return dcc.send_data_frame(df.to_csv, "table.csv", index = False)


@app.callback(
    Output('selected_trace', 'data'),
    Input('datatable', 'active_cell'),
    State("tab2_param1","value"),
    State("tab2_param2","value"),
    State("no_of_parameters","value"),
)
def store_selected_trace(active_cell, param1, param2, n_params):
    if n_params == 2 and param1 and param2 and active_cell:
        active_row = active_cell['row']+1
        particle_n = f"Particle {active_row}"
        df = pd.read_csv('particles.csv')
        x = list(df[param1][df['Particles'] == particle_n])[0]
        y = list(df[param2][df['Particles'] == particle_n])[0]
        return [x, y]
    else:
        return None


app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="trigger_hover"),
    Output("dummy", "data-hover"),
    [Input('selected_trace', 'data')],
)



if __name__ == '__main__':
    app.run_server(host='localhost',port=8222)

