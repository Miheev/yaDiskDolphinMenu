#!/bin/bash

# Set up path variables here
# Simple paths without whitespaces expected
# Example:
# - YA_DISK_ROOT = $HOME/Public
# - YA_DISK_RELATIVE = 'yaDisk', computed path: $HOME/Public/yaDisk
# - INBOX_RELATIVE = 'Media', computed path: $HOME/Public/yaDisk/Media
#
# Prefix relative paths with \ e.g. 'path\/to\/dir'
#
YA_DISK_ROOT=$HOME/Public
YA_DISK_RELATIVE='yaDisk'
INBOX_RELATIVE='Media'
LOG_PATH='$YA_DISK_ROOT/yaMedia.log'

cd "$(dirname $0)"
echo "working directory changed to $PWD"

# Set global static YA_DISK_ROOT var
echo "Root access required to set global static YA_DISK_ROOT var"
isRootSetString=$( grep ^YA_DISK_ROOT= /etc/environment | tail -1 )
if [ -z "$isRootSetString" ]; then
  echo "YA_DISK_ROOT=$YA_DISK_ROOT" | sudo tee -a /etc/environment
else
  echo ""
  tac /etc/environment | awk -v dest="YA_DISK_ROOT=\"$YA_DISK_ROOT\"" "!x{x=sub(/^YA_DISK_ROOT=.*/,dest)}1" | tac | sudo tee /etc/environment
  echo ""
fi

echo "Set local script-scoped vars"
output=$( awk -v line="yaDisk=\$YA_DISK_ROOT/$YA_DISK_RELATIVE;" "!x{x=sub(/^yaDisk=.*/,line)}1" ./ydmenu.sh | awk -v line="streamDir=\$yaDisk/$INBOX_RELATIVE;" "!x{x=sub(/^streamDir=.*/,line)}1" | awk -v line="logFilePath=$LOG_PATH;" "!x{x=sub(/^logFilePath=.*/,line)}1" )
echo "$output" > ./ydmenu.sh
output=$( awk -v line="tee -a $LOG_PATH" "{gsub(/tee -a.*/,line)}1" ./ydpublish.desktop )
echo "$output" > ./ydpublish.desktop

echo "Create symlinks accordingly"
serviceMenu=$HOME/.local/share/kservices5/ServiceMenus
if [ ! -L $serviceMenu/ydpublish.desktop ]; then
  desktopBak=$serviceMenu/ydpublish.desktop.bak
  if [ -f $desktopBak ]; then
    echo "Backup already exist: $desktopBak"
  else
    echo "Create backup for default desktop file $desktopBak"
    mv $serviceMenu/ydpublish.desktop $desktopBak
  fi

  ln -s "$PWD/ydpublish.desktop" $serviceMenu
fi
if [ ! -L $HOME/bin/ydmenu.sh ]; then
  ln -s "$PWD/ydmenu.sh" $HOME/bin
fi

echo "Done"