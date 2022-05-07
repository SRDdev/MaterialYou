import os
from unicodedata import name
from fastapi import FastAPI , File, Request , UploadFile
from starlette.routing import Host
# import gunicorn
import uvicorn
import numpy as np
import cv2
import os 
from io import BytesIO
from PIL import Image
from sklearn.cluster import KMeans
from collections import Counter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()
app.mount("/static",StaticFiles(directory="static"),name="static")
templates = Jinja2Templates(directory="templates")

#-------------------------------------Functions---------------------------------#
def get_ids(color, id_prefix, percentage=[20, 100 ,70, 10],shade=[False, True, True, False]):
    ids = []
    for index in range(4):
        ids.append({
            #colours_primary_0
            "id":"colours_" + id_prefix + "_" +str(index), 
            "color":color,
            "tint":str(shade[index]),
            "percentage":percentage[index]
        })
    return ids

def get_ids_color(color, id_prefix, percentage=[100,90,80,70,60,50,40,30,20,10,10,20,30,40,50,60,70,80,90,100],shade=[True,True,True,True,True,True,True,True,True,True,False,False,False,False,False,False,False,False,False,False]):
    ids = []
    for index in range(20):
        ids.append({
            #colours_primary_0
            "id":"colours_" + id_prefix + "_" +str(index), 
            "color":color,
            "tint":str(shade[index]),
            "percentage":percentage[index]
        })
    return ids

def get_image(image_path):
    image = cv2.imread(image_path)
    # image = image.resize((round(image.size[0]*0.5), round(image.size[1]*0.5)))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

def RGB_HEX(color):
    return "#{:02x}{:02x}{:02x}".format(int(color[0]),int(color[1]),int(color[2]))

def RGB_RGBA(color):
    return "#{:02x}{:02x}{:02x}".format("#{02x}{:02x}{:02x}{:02x}")

def get_colors(image, number_of_colors, show_chart):
    modified_image = cv2.resize(image , (800, 800), interpolation = cv2.INTER_AREA)
    modified_image = modified_image.reshape(modified_image.shape[0]*modified_image.shape[1],3)
    
    clf = KMeans(n_clusters = number_of_colors)
    labels = clf.fit_predict(modified_image)
    try : 
        counts = Counter(labels)
        # sort to ensure correct color percentage
    except:
        pass
    counts = dict(sorted(counts.items()))

    center_colors = clf.cluster_centers_
    # We get ordered colors by iterating through the keys
    global hex_colors,hex
    global rgb_colors
    ordered_colors = [center_colors[i] for i in counts.keys()]
    hex_colors = [RGB_HEX(ordered_colors[i]) for i in counts.keys()]
    rgb_colors = [(ordered_colors[i]) for i in counts.keys()]
    hex=list(hex_colors)
    hex.sort()
    return hex

def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image

#-------------------------------------Request---------------------------------#
@app.route("/")
async def home(request: Request):
    return templates.TemplateResponse('main.html', context={'request': request})

@app.route("/home")
async def palette(request:Request):
    return templates.TemplateResponse('home.html', context={'request': request,'result': hex})

@app.route("/scheme")
async def scheme(request:Request):
    return templates.TemplateResponse('scheme-home.html', context={'request': request,'result': hex})

@app.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    global image
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0)
    get_colors(image,4, False)
    primary = json.dumps(get_ids(hex[0], "primary"))
    secondary = json.dumps(get_ids(hex[1], "secondary"))
    tertiary = json.dumps(get_ids(hex[2], "tertiary"))
    error = json.dumps(get_ids(hex[3], "error"))
    props = {
        'request': request, 
        'primary':primary, 
        'secondary':secondary, 
        'tertiary':tertiary, 
        'error':error,
    }
    return templates.TemplateResponse('palette.html', context=props)

@app.post("/colors")
async def predict(request: Request, file: UploadFile = File(...)):
    global image
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0)
    get_colors(image,4, False)
    primary = json.dumps(get_ids_color(hex[0], "primary"))
    secondary = json.dumps(get_ids_color(hex[1], "secondary"))
    tertiary = json.dumps(get_ids_color(hex[2], "tertiary"))
    error = json.dumps(get_ids_color(hex[3], "error"))
    props = {
        'request': request, 
        'primary':primary, 
        'secondary':secondary, 
        'tertiary':tertiary, 
        'error':error
    }
    return templates.TemplateResponse('scheme.html', context=props)

if __name__ == "__main__":
   uvicorn.run(app, host='localhost', port=8080)