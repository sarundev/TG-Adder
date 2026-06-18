import os

application = 'dist/TELE168.app'
appname = os.path.basename(application)

format = 'UDZO'
files = [application]
symlinks = {'Applications': '/Applications'}
