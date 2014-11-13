import hashlib
import json
import os

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, send_from_directory
from werkzeug import secure_filename

DEBUG = True

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
BOX_ROOT = os.path.join(APP_ROOT, 'boxes')

SERVER_NAME = "localhost:5000"

BOX_EXTENSION = "box"

HOST_VAR = "${hostname}"

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
    metadata = metadata.replace(app.config['HOST_VAR'], app.config['SERVER_NAME'])
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
  
  
@app.route('/boxes/<path>/<version>/<provider>/<file>/')
def downloadBox(path, version, file, provider):
  boxHome = os.path.join(app.config['BOX_ROOT'], path)
  boxVersion = os.path.join(boxHome, version)
  boxProvider = os.path.join(boxVersion, provider)
  if request.headers.get('User-Agent').startswith("Vagrant"):
    return send_from_directory(directory=boxProvider, filename=file)
  else:
    return send_from_directory(directory=boxProvider, filename=file)

#
# Upload boxes
#

@app.route('/upload/new_box/')
def craeteBox():
  return render_template('new_box.html')

@app.route('/upload/uploaded/', methods=['POST'])
def processUpload():
        app.logger.debug("Upload")
        title = ""
      
        file = request.files['boxFile']
        filename = secure_filename(file.filename)
        version = request.form['version']
        box = request.form['box']
        provider = request.form['provider']

        message = ""

        if file and allowed_file(filename):
            if request.form['upload'] == "box":
                app.logger.debug("Box")
                title = "Upload Box"
                description = request.form['description']
                processCreateBox(file, filename, version, box, provider, description)
            elif request.form['upload'] == "version":
                app.logger.debug("version")
                title = "Upload Version"
                message = processCreateVersion(file, filename, version, box, provider)
            elif request.form['upload'] == "provider":
                app.logger.debug("provider")
                title = "Upload Provider"
        else:  
            message = "File not found, or not a *.box file"        
    
        return render_template('uploaded.html', title=title, message=message)

@app.route('/upload/version', methods=['POST'])
def addVersion():
    app.logger.debug("add version")
    box = request.form['box']
    return render_template('upload.html', uploadType="version", boxName=box)

@app.route('/upload/provider', methods=['POST'])
def addProvider():
    app.logger.debug("add providers")
    box = request.form['box']
    version = request.form['version']
    return render_template('upload.html', uploadType="provider", boxName=box, version=version)

@app.route('/upload/box', methods=['POST'])
def addBox():
    app.logger.debug("add box")
    return render_template('upload.html', uploadType="box", version="0", description=True)

@app.route('/upload/')
def generalUpload():
    app.logger.debug("general upload")
    return render_template('upload.html', uploadType="box", version="0", description=True)

#
# Process Upload Methods
#

def processCreateBox(file, filename, version, box, provider, description):
    app.logger.debug("process create box")
    message = ""
    boxHome = os.path.join(app.config['BOX_ROOT'], box)
    if os.path.isdir(boxHome):
        message = "Box already exists"
    else:
        
        newVersion = saveBox(file, filename, provider, box, version)

        metadata = {}
        metadata["name"] = box
        metadata["description"] = description
        versions = []

        versions.insert(0, newVersion)
        metadata["versions"] = versions

        saveBoxMetadata(box, metadata)
    
    return message


def processCreateVersion(file, filename, version, box, provider):
    app.logger.debug("process create version")
    message = ""
    metadata = json.loads(getBoxMetadataFile(box).read())
            
    if versionLegal(version, metadata, provider):

        newVersion = saveBox(file, filename, provider, box, version)
        addOrUpdateVersion(metadata, newVersion)
        saveBoxMetadata(box, metadata)
        message = "Sucessfully uploaded version :" + version + " to box: " + box + " for provider: " + provider
    else:
        message = "Version/Provider already in exists"
    return message

def processCreateProvider(file, filename, version, box, provider):
    app.logger.debug("Process create provider")
    message = ""
    metadata = json.loads(getBoxMetadataFile(box).read())
            
    if versionLegal(version, metadata, provider, True):

        newVersion = saveBox(file, filename, provider, box, version)
        addOrUpdateVersion(metadata, newVersion)
        saveBoxMetadata(box, metadata)
        message = "Sucessfully uploaded provider :" + provider
    else:
        message = "Provider already exists, or version does not"
    return message


#
# Utilities
#

def getBoxMetadataFile(box, mode='r'):
    boxHome = os.path.join(app.config['BOX_ROOT'], box)
    if os.path.isdir(boxHome):        
        metadataFile = os.path.join(boxHome, 'metadata.json')
        f = open(metadataFile, mode)
        return f

def saveBoxMetadata(box, metadata):
    f = getBoxMetadataFile(box, 'w')
    data = json.dumps(metadata, sort_keys=True, indent=4, separators=(',', ': '))
    f.write(data)
    f.close()
    
def saveBox(file, filename, provider, box, version):
    boxHome = os.path.join(app.config['BOX_ROOT'], box)
    boxVersion = os.path.join(boxHome, version)
    boxProvider = os.path.join(boxVersion, provider)
                    
    os.makedirs(boxProvider)
                   
    filePath = os.path.join(boxProvider, filename)
    file.save(filePath)
    return processFile(filePath, filename, provider, box, version)
       
def getBoxes():
    boxes=[]
    for folder in os.listdir(app.config['BOX_ROOT']):
        boxes.append(folder)
    return boxes

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] == BOX_EXTENSION
          

def versionLegal(version, metadata, provider, requireVersion=False):
    for curVersion in metadata["versions"]:
        if curVersion["version"] == version:
            for curProvider in curVersion['providers']:
                if curProvider == provider:
                    return False
            return requireVersion
    return not requireVersion

def processFile(filepath, filename, provider, box, version):
    app.logger.debug("process file")
    sha1 = hashlib.sha1()
    f = open(filepath, 'rb')
    try:
    
        sha1.update(f.read())

        url = "http://" + app.config['HOST_VAR'] + "/boxes/"  + box + "/" + version + "/" + provider + "/" +  filename

        providerDetails = {}
        providerDetails["name"] = provider
        providerDetails["url"] = url
        providerDetails["checksum_type"] = "sha1"
        providerDetails["checksum"] = sha1.hexdigest()

        newVersion = {'version':version, 'providers':[providerDetails]}
        
        return newVersion
      
    finally:
        f.close()

def addOrUpdateVersion(metadata, versionJson):
    for curVersion in metadata["versions"]:
        if curVersion["version"] == versionJson["version"]:
            curVersion["providers"].extend(versionJson["providers"])
            return
    metadata["versions"].append(versionJson)

if __name__ == "__main__":
  app.run()
