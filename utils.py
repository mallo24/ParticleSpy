import numpy as np
from dash import html

def process_image(im_hs):
    im = im_hs.data.astype(np.float64)
    im = im-np.min(im)
    image = np.uint8(255*im/np.max(im))
    return image

def get_data_of_param(particles,param):
    return [i.properties[param]['value'] if param.find(",")==-1 else i.properties[param.split(",")[0] and param.split(",")[1]]['value'] for i in particles.list]

def make_table(df):
    cols=df.columns
    table_head=html.Thead(html.Tr([html.Th(i.title()) if i!='equivalent circular diameter' else html.Th('Diameter') for i in cols]))
    table_body_elements=[]
    for _,row in df.iterrows():
        table_row_elements=[]
        for col in cols:
            t=row[col]
            if type(t)==float:
                t=round(t,3)
            if t=='inf':
                t=''
            table_row_elements.append(html.Td(t))
        table_row=html.Tr(table_row_elements)
        table_body_elements.append(table_row)
    table_body=html.Tbody(table_body_elements)
    return [table_head,table_body]

def make_data(particles):
    particles_col=['Particle '+str(i) for i in range(1,len(particles.list)+1)]
    data={'Particles':particles_col}
    col_names=list(particles.list[0].properties.keys())
    col_names.remove('frame')
    for param in col_names:
        data[param]=get_data_of_param(particles,param)
    return data