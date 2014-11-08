import json
import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, send_from_directory
from werkzeug import secure_filename
import hashlib


DEBUG = True

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
BOX_ROOT = os.path.join(APP_ROOT, 'boxes')

SERVER_NAME = "localhost:5000"

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
def processUpload():
        print "Upload"
        title = ""
        message = "Hi?"
      
        if request.form['upload'] == "box":
            print "Box"
        elif request.form['upload'] == "version":
            title = "upload box"
            
            file = request.files['boxFile']
            filename = secure_filename(file.filename)
            version = request.form['version']
            box = request.form['box']
            provider = request.form['provider']
            metadata = json.loads(getBoxMetadataFile(box).read())
            
            if versionLegal(version, metadata, provider):
            
                  boxHome = os.path.join(app.config['BOX_ROOT'], box)
                  boxVersion = os.path.join(boxHome, version)
                                    
                  os.makedirs(boxVersion)
                  print boxVersion
                  
                  if file and allowed_file(filename):                  
                        filePath = os.path.join(boxVersion, filename)
                        file.save(filePath)
                        newVersion = processFile(filePath, filename, provider, box, version)
                        print newVersion
                        addOrUpdateVersion(metadata, newVersion)
                        print metadata
                        saveBoxMetadata(box, metadata)
                        message = "Sucessfully uploaded version :" + version + " to box: " + box + " for provider: " + provider
                  else:
                    message = "Illegal file"
            else:
                print "version illegal"
                message = "Version/Provider already in exists"
        
        elif request.form['upload'] == "provider":
            print "provider"
            
        return render_template('uploaded.html', title=title, message=message)

@app.route('/upload/version', methods=['POST'])
def addVersion():
    print app.config['SERVER_NAME']
    box = request.form['box']
    return render_template('upload.html', uploadType="version", boxName=box)

@app.route('/upload/provider', methods=['POST'])
def addProvider():
    print app.config['SERVER_NAME']
    box = request.form['box']
    version = request.form['version']
    return render_template('upload.html', uploadType="provider", boxName=box, version=version)

@app.route('/upload/box', methods=['POST'])
@app.route('/upload')
def addBox():
    print app.config['SERVER_NAME']
    return render_template('upload.html', uploadType="box")

#
# Process Upload Methods
#

def processCreateBox():
    print "process create box"

def processCreateVersion():
    print "process create version"

def processCreateProvider():
    print "Process create provider"


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
    
       
def getBoxes():
    boxes=[]
    for folder in os.listdir(app.config['BOX_ROOT']):
        boxes.append(folder)
    return boxes

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] == BOX_EXTENSION
          

def versionLegal(version, metadata, provider):
    for curVersion in metadata["versions"]:
        if curVersion["version"] == version:
            for curProvider in curVersion['providers']:
                if curProvider == provider:
                    return False
            return False
    return True

def processFile(filepath, filename, provider, box, version):
    print "process file"
    sha1 = hashlib.sha1()
    f = open(filepath, 'rb')
    try:
    
        sha1.update(f.read())

        url = "http://" +app.config['SERVER_NAME'] + "/boxes/"  + box + "/" + version + "/" +  filename

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
