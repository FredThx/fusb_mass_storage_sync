from version import __version__
with open("properties.txt","r") as file:
    properties = file.read()
properties = properties.replace("__version__","'" + __version__ + "'")
with open("properties.rc",'w') as file:
    file.write(properties)
