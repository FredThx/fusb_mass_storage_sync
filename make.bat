@echo off
python make_properties.py
pyinstaller ^
  -wF ^
  --add-data="icon.png;icon.png" ^
  --icon=.\icon.png ^
  --version-file=properties.rc ^
  --name fusb_sync ^
  fusb_mass_storage_sync.py
pause
