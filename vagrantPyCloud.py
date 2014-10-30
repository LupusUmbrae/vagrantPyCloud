import json
import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, send_from_directory
from werkzeug import secure_filename


DEBUG = True

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
BOX_ROOT = os.path.join(APP_ROOT, 'boxes')

BOX_EXTENSION = "box";

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def show_entries():
  return render_template('home.html')

#
# View box methods
#

@app.route('/boxes/')
def listBox():
  boxes=getBoxes()
  return render_template('boxes.html', boxes=boxes)

@app.route('/boxes/<path>/')
def box(path):
  f = getBoxMetadataFile(path)
  if f is None:
    return render_template('box.html', boxName="Unknown box: " + path, description="This is not the box you are looking for", versions=[])
  elif request.headers.get('User-Agent').startswith("Vagrant"):
    metadata = f.read()
    return Response(metadata,  mimetype='application/json')
      
  else:
    contents = f.read()
    metadata = json.loads(contents)      
    return render_template('box.html', boxName=metadata['name'], description=metadata['description'], versions=metadata['versions'])

@app.route('/boxes/<path>/<versionNumber>/')
def boxVersion(path, versionNumber):
  f = getBoxMetadataFile(path)
  metadata = json.loads(f.read())
  version = None
  for curVersion in metadata['versions']:
    if curVersion['version'] == versionNumber:
      version = curVersion
      break
  
  return render_template('version.html', boxName=metadata['name'], description=metadata['description'], version=versionNumber, providers=version['providers'])
  
  
@app.route('/boxes/<path>/<version>/<file>/')
def downloadBox(path, version, file):
  boxHome = os.path.join(app.config['BOX_ROOT'], path)
  boxVersion = os.path.join(boxHome, version)
  if request.headers.get('User-Agent').startswith("Vagrant"):
    return send_from_directory(directory=boxVersion, filename=file)
  else:
    return send_from_directory(directory=boxVersion, filename=file)

#
# Upload boxes
#

@app.route('/upload/new_box/')
def craeteBox():
  return render_template('new_box.html')

@app.route('/upload/uploaded/', methods=['POST'])
def upload():
  print "hello"
  boxName = request.form['box']
  print boxName
  if request.form['upload'] == "box":
    print "upload box"
    
    file = request.files['boxFile']
    version = request.form['version']
    box = request.form['box']
    
    boxHome = os.path.join(app.config['BOX_ROOT'], box)
    boxVersion = os.path.join(boxHome, version)
    
    print "Making dirs"
    
    os.makedirs(boxVersion)
    print boxVersion
    
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      file.save(os.path.join(boxVersion, filename))
  elif request.form['upload'] == "create":
    print "create box"
  return render_template('uploaded.html')

@app.route('/upload/version', methods=['POST'])
def addVersion():
  box = request.form['box']
  return render_template('add_version.html', boxName=box)

@app.route('/upload/provider', methods=['POST'])
def addProvider():
  return render_template('new_provider.html')


#
# Utilities
#

def getBoxMetadataFile(box):
  boxHome = os.path.join(app.config['BOX_ROOT'], box)
  if os.path.isdir(boxHome):
    metadataFile = os.path.join(boxHome, 'metadata.json')
    f = open(metadataFile, 'r')
    return f
       
def getBoxes():
  boxes=[]
  for folder in os.listdir(app.config['BOX_ROOT']):
    boxes.append(folder)
  return boxes

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] == BOX_EXTENSION
          

def versionLegal(version, metadata):
  for curVersion in metadata["versions"]:
    if curVersion["version"] == version:
      return false
  return true
  

if __name__ == "__main__":
  app.run()
