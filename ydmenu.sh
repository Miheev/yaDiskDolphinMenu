#!/bin/bash
# 
# Yandex Disk menu actions logic
# Spec https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-1.0.html#basic-format
#

commandType=$1;
# Spec params
F=$2;
# k=$3;
c=$4;

# Dialog params
yaIcon='/usr/share/yd-tools/icons/yd-128.png';
yaErrorIcon='/usr/share/yd-tools/icons/light/yd-ind-error.png';
yaTitle='Yandex.Disk';

# Src params
srcFilePath=$F;
fileName=$(basename "$F");
filePath=$(dirname "$F");

# Dest params
yaDisk=$YA_DISK_ROOT/yaMedia;
streamDir=$yaDisk/Media;
yaDiskFilePath="$yaDisk/$fileName";
streamFilePath="$streamDir/$fileName";

extPart='';
fileNamePart='';
if [ "${fileName::1}" = '.' ]; then
  fileNamePart="${fileName}";
else
  extPart=".${fileName#*.}";
  fileNamePart="${fileName%%.*}";    
fi

# Is src outside of the root directory in sync?
isOutsideFile=1;
if [[ "$srcFilePath" = "$yaDisk/"* ]]; then
  isOutsideFile=0;
fi

timestamp=$(date +%s);
# kdialog --passivepopup "  " 15;


# Show info message
# $1 String: message
# $2 Number: timeout
function showMsg(){
  kdialog --icon=$yaIcon --title=$yaTitle --passivepopup "$1 \n Time: $(expr $(date +%s) - $timestamp)" $2;
}

# Show info message
# $1 String: message
function showError(){
  kdialog --icon=$yaErrorIcon --title=$yaTitle --passivepopup "$1 \n Time: $(expr $(date +%s) - $timestamp)" 15;
}

# Wait for the yandex-disk daemon ready for interactions
function waitForReady() {
  local statusString=$( yandex-disk status | grep -m1 status ); 
  local statusCode="${statusString#*: }";
  local waitCount=30;
  
  if [ "$statusCode" = 'idle' ]; then
    return ;
  fi
  
  showError "<b>Service status: $statusCode</b>. \n Will wait for <b>$(echo $waitCount)s</b> and exit if no luck.";
  
  local index=0;
  while [[ "$statusCode" != 'idle' && $index -lt $waitCount ]]; do    
    statusString=$( yandex-disk status | grep -m1 status ); 
    statusCode="${statusString#*: }";    
    ((++index));
    sleep 1;
  done
  
  if [ "$statusCode" != 'idle' ]; then
    showError "<b>Service is not available</b>. \n Try later or restart it via \n <b><i>yandex-disk stop && ayndex-disk start</i></b>.";
    exit 1;
#   else
#     showMsg "Service is ready: $statusCode.";
  fi
}


# Save clipboard content to file
function copyFromClipboard() {
  local currentDate=$(date '+%Y-%m-%d %H:%M:%S');
  local targetType=$(xclip -selection clipboard -t TARGETS -o | grep -m1 ^image);
  local fullPath='note-';

  if [ -z $targetType ]; then
    # Trim non-file character and form file name from note
    # File name rules: https://www.cyberciti.biz/faq/linuxunix-rules-for-naming-file-and-directory-names/
    # single quote: \047,
    # & not listed for usability, but should be present as described in doc above
    #
    # Take name from note example
    # nameSummary="as||d:< asdas?/*<, >, |, \, :, (, ), &, ;,*\ 'k\&fsldf' 047 7878667"; nameSummary=$( echo "${nameSummary//+([<>|\\:\/()&;,])/''}" | xargs | cut -c1-30 ); echo "=$nameSummary=";
    local nameSummary=$(xclip -selection clipboard -o | head -1 | awk '{gsub(/([<>|\\\;\/(),"\047])|(https?:)|(:)|( {2})|([ \.]+$)/,"")}1' | xargs | cut -c1-30 );
    if [ ! -z "$nameSummary" ]; then
      nameSummary=" $nameSummary";
    fi

    fullPath="$streamDir/$fullPath$currentDate$nameSummary.txt";
    xclip -selection clipboard -o > "$fullPath";
  else
    fullPath="$streamDir/$fullPath$currentDate.$(basename $targetType)";
    xclip -selection clipboard -t $targetType -o > "$fullPath";    
  fi
  
  echo "$fullPath";
}

# Publish file and copy link to international (*.com) or local (*.ru) location zone. RU link is shortened by default
# $1 String: file path to publish
# $2 Boolean: copy international link ?
function publishWithComZone() {
  local publishPath=$( yandex-disk publish "$1" );
  local comLink="https://disk.yandex.com${publishPath#*.sk}";

  if (( $2 )); then
    echo "$comLink" | xclip -filter -selection clipboard;
  else
    echo "$publishPath" | xclip -filter -selection clipboard;
  fi

  showMsg "Public link to the $1 is copied to the clipboard. \n <a href='$comLink'><b>$comLink</b></a> \n <a href='$publishPath'><b>$publishPath</b></a>" 15;
}

# Unpublish file and its copies from the stream directory. 
# If file is outside of the root directory in sync, the function will try to find it in the stream directory
# $1 String: directory without fileName where copies are located
# $2 String: the main file for finding dublicates
function unpublishCopyList() {
  local baseDir=$1;
  local nextFile=$2;
  local nextFileName=$fileName;
  
  local index=0;
  local indexPart='';
  local unpublishRes='';
  local $res='';
  while [ -f "$nextFile" ]; do
    res=$( yandex-disk unpublish "$nextFile" );
    unpublishRes+="<b>$nextFileName</b> - $res; \n";
    
    ((++index));
    indexPart="_$index";  
    nextFileName="$fileNamePart$indexPart$extPart";
    nextFile="$baseDir/$nextFileName";
#     waitForReady;
  done
  
  echo "$unpublishRes";
}


waitForReady


# Rename file if already exist in the destination and temporal directories
isFileNameChanged=0;
if [[ ( -f "$streamFilePath" || -f "$yaDiskFilePath" ) && ( ( $isOutsideFile = 1 && $commandType = "PublishToYandex"* ) || $commandType = "File"* ) ]]; then
  index=0;
  indexPart='';
  srcFilePath='';
  while [ -f "$streamFilePath" ] || [ -f "$yaDiskFilePath" ] || [ -f "$srcFilePath" ]; do
    ((++index));
    indexPart="_$index";  
    fileName="$fileNamePart$indexPart$extPart";
    yaDiskFilePath="$yaDisk/$fileName";
    streamFilePath="$streamDir/$fileName";
    srcFilePath="$filePath/$fileName";
  done

  mv "$F" "$srcFilePath";
  isFileNameChanged=1;
#   kdialog --passivepopup "$fileName $yaDiskFilePath \n $streamFilePath " 15;
fi
# elif [[ "$streamFilePath" != $F && "$yaDiskFilePath" = $F ]]; then
#   "yaDiskFilePath = srcFilePath. \n <b>Skip for now, mv and cp inside ya disk directory is unstabled</b>: \nit leads to sync process hangs and broken public links, if combined with publish."


# Publish actions
if [[ $commandType = 'PublishToYandexCom' || $commandType = 'PublishToYandex' ]]; then
  isComLink=1;
  if [ $commandType = 'PublishToYandex' ]; then
    isComLink=0;
  fi
  
  publishWithComZone "$srcFilePath" $isComLink;  
  (( isOutsideFile )) && mv "$yaDiskFilePath" $streamDir;
elif [[ $commandType = 'ClipboardPublishToCom' || $commandType = 'ClipboardPublish' ]]; then 
  clipDestPath=$(copyFromClipboard);
  showMsg "Clipboard flushed to stream: \n <b>$clipDestPath</b> \n $(yandex-disk sync)" 5;
  
  isComLink=1;
  if [ $commandType = 'ClipboardPublish' ]; then
    isComLink=0;
  fi

  waitForReady;
  publishWithComZone "$clipDestPath" $isComLink;


# Unpublish actions
elif [ $commandType = 'UnpublishFromYandex' ]; then
  unpublishRes='';
  if (( isOutsideFile )); then
    unpublishRes=$( yandex-disk unpublish "$streamFilePath" );    
  else
    unpublishRes=$( yandex-disk unpublish "$srcFilePath" );    
  fi
  showMsg "$unpublishRes for <b>$fileName</b>." 5
elif [ $commandType = 'UnpublishAllCopy' ]; then
  unpublishRes='';
  if (( isOutsideFile )); then
    unpublishRes=$( unpublishCopyList "$streamDir" "$streamFilePath" );
  else
    unpublishRes=$( unpublishCopyList "$filePath" "$srcFilePath" );
  fi
  showMsg "Files unpublished: \n $unpublishRes" 5

  
# Copy & move actions without publishing
elif [ $commandType = 'ClipboardToStream' ]; then
  showMsg "Clipboard flushed to stream: \n <b>$( copyFromClipboard )</b> \n `yandex-disk sync`" 10;
elif [ $commandType = 'FileAddToStream' ]; then
  cp -rf "$srcFilePath" $streamDir; 
  showMsg "<b>$srcFilePath</b> is copied to the file stream. \n `yandex-disk sync`" 5;
elif [ $commandType = 'FileMoveToStream' ]; then
  mv -f "$srcFilePath" $streamDir;
  showMsg "<b>$srcFilePath</b> is moved to the file stream. \n `yandex-disk sync`" 5;    
else
  workPath="$HOME/.local/share/kservices5/ServiceMenus";
  showMsg "<b>Unknown action $commandType</b>. \n\n Check <i>$workPath/$c</i> for available actions." 15;
fi


# Rename back if file name has been changed
if (( isFileNameChanged )) && [ -f "$srcFilePath" ]; then
  mv "$srcFilePath" "$F";
fi
