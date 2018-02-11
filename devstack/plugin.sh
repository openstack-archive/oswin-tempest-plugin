#!/bin/bash

DIR_OSWIN_TEMPEST_PLUGIN=$DEST/oswin-tempest-plugin

if [[ "$1" == "stack" && "$2" == "install" ]]; then
  cd $DIR_OSWIN_TEMPEST_PLUGIN
  echo "Installing oswin-tempest-plugin"
  setup_develop $DIR_OSWIN_TEMPEST_PLUGIN

  echo "Sucessfully installed oswin-tempest-plugin"

fi
