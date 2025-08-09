#!/bin/bash
# 
# Yandex Disk menu actions logic
# Spec https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-1.0.html#basic-format
#

commandType=$1
# Spec params
F=$2
# k=$3;
c=$4

# Dialog params
yaIcon='/usr/share/yd-tools/icons/yd-128.png'
yaWarnIcon='/usr/share/yd-tools/icons/yd-128_g.png'
yaErrorIcon='/usr/share/yd-tools/icons/light/yd-ind-error.png'
yaTitle='Yandex.Disk'

# Src params
srcFilePath=$F
fileName=$(basename "$F")
filePath=$(dirname "$F")

# Dest params
yaDisk=$YA_DISK_ROOT/yaMedia
streamDir=$yaDisk/Media
logFilePath=$YA_DISK_ROOT/yaMedia.log
yaDiskFilePath="$yaDisk/$fileName"
streamFilePath="$streamDir/$fileName"

extPart=''
fileNamePart=''
if [ "${fileName::1}" = '.' ]; then
  fileNamePart="${fileName}"
else
  extPart=".${fileName#*.}"
  fileNamePart="${fileName%%.*}"
fi

# Is src outside of the root directory in sync?
isOutsideFile=1
if [[ "$srcFilePath" = "$yaDisk/"* ]]; then
  isOutsideFile=0
fi

timestamp=$(date +%s);
echo -e "\nStatus: Start $(date '+%Y-%m-%d %H:%M:%S')"
# kdialog --passivepopup "  " 15;


# Mock for tests
#function yandex-disk() {
#  echo "status: idle"
#}

# Rename back if file name has been changed
function renameBack() {
  if (( isFileNameChanged )) && [ -f "$srcFilePath" ]; then
    mv "$srcFilePath" "$F"
  fi
}

# Show info message ang log it
# $1 String: message
# $2 Number: timeout
function showMsg(){
  kdialog --icon=$yaIcon --title=$yaTitle --passivepopup "$1 \n Time: $(expr $(date +%s) - $timestamp)" $2
  echo "$1";
}

# Show info message with long text
# $1 String: message
function showLongMsg(){
  kdialog --icon=$yaIcon --title=$yaTitle --passivepopup "$1 \n Time: $(expr $(date +%s) - $timestamp)" 15
}

# $1 String: message
function showWarn(){
  kdialog --icon=$yaWarnIcon --title=$yaTitle --passivepopup "$1" 15
}

# $1 String: message
function showError(){
  kdialog --icon=$yaErrorIcon --title=$yaTitle --passivepopup "$1 \n See <a href='file://$logFilePath'>log</a> for details \n Time: $(expr $(date +%s) - $timestamp)" 15
}

# Show error and exit
# $1 String: message
# $2 String: additional log message
function showException() {
    showError "$1"

    if [ -z "$2" ]; then
      echo "$1"
    else
      echo "$2"
    fi

    renameBack
    echo "Status: Error $(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
}

# Wait for the yandex-disk daemon ready for interactions
function waitForReady() {
  local statusString=$( yandex-disk status | grep -m1 status )
  local statusCode="${statusString#*: }"
  local waitCount=30

  if [ -z "$statusCode" ]; then
    statusCode='not started'
  fi
  if [ "$statusCode" = 'idle' ]; then
    return ;
  fi
  
  showWarn "<b>Service status: $statusCode</b>. \n Will wait for <b>$(echo $waitCount)s</b> and exit if no luck."
  
  local index=0
  while [[ "$statusCode" != 'idle' && $index -lt $waitCount ]]; do    
    statusString=$( yandex-disk status | grep -m1 status )
    statusCode="${statusString#*: }"
    ((++index))
    sleep 1
  done

  if [ "$statusCode" != 'idle' ]; then
    showException "<b>Service is not available</b>. \n Try later or restart it via \n <b><i>yandex-disk stop && yandex-disk start</i></b>." "Service is not available"
#   else
#     showMsg "Service is ready: $statusCode.";
  fi
}


# Check if current session is Wayland
function is_wayland_session() {
  [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]
}

# Generate a safe, short summary from text for filename suffix
function generate_name_summary() {
  local clip_text="$1"
  echo "$clip_text" | head -1 | awk '{gsub(/([<>|\\;\/(),"\047])|(https?:)|(:)|( {2})|([ \.]+$)/,"")}1' | xargs | cut -c1-30 | iconv -c
}

# Save clipboard content to file (X11 implementation)
function copyFromClipboardX11() {
  local currentDate="$1"
  local targetType=$(xclip -selection clipboard -t TARGETS -o | grep -m1 ^image)
  local fullPath='note-'

  if [ -z "$targetType" ]; then
    # Handle text content
    local clip_text=$(xclip -selection clipboard -o)
    local nameSummary=$(generate_name_summary "$clip_text")
    if [ ! -z "$nameSummary" ]; then
      nameSummary=" $nameSummary"
    fi
    
    fullPath="$streamDir/$fullPath$currentDate$nameSummary.txt"
    xclip -selection clipboard -o > "$fullPath"
  else
    # Handle image content
    fullPath="$streamDir/$fullPath$currentDate.$(basename $targetType)"
    xclip -selection clipboard -t $targetType -o > "$fullPath"
  fi
  
  echo "$fullPath"
}

# Save clipboard content to file (Wayland implementation)
function copyFromClipboardWayland() {
  local currentDate="$1"
  local targetType=$(wl-paste --list-types | grep -m1 ^image/)
  local fullPath='note-'

  if [ -z "$targetType" ]; then
    # Handle text content
    local clip_text=$(wl-paste)
    local nameSummary=$(generate_name_summary "$clip_text")
    if [ ! -z "$nameSummary" ]; then
      nameSummary=" $nameSummary"
    fi
    
    fullPath="$streamDir/$fullPath$currentDate$nameSummary.txt"
    wl-paste > "$fullPath"
  else
    # Handle image content
    fullPath="$streamDir/$fullPath$currentDate.$(basename $targetType)"
    wl-paste --type "$targetType" > "$fullPath"
  fi
  
  echo "$fullPath"
}

# Save clipboard content to file (action wrapper)
function copyFromClipboard() {
  local currentDate=$(date '+%Y-%m-%d %H:%M:%S')
  local fullPath
  
  # Trim non-file character and form file name from note
  # File name rules: https://www.cyberciti.biz/faq/linuxunix-rules-for-naming-file-and-directory-names/
  # single quote: \047,
  # & not listed for usability, but should be present as described in doc above
  #
  # Take name from note example
  # nameSummary="as||d:< asdas?/*<, >, |, \, :, (, ), &, ;,*\ 'k\&fsldf' 047 7878667"; nameSummary=$( echo "${nameSummary//+([<>|\\:\/()&;,])/''}" | xargs | cut -c1-30 ); echo "=$nameSummary=";
  #
  # Linux bug: multi-byte handling to upstream coreutils, 2006 year
  # https://lists.gnu.org/archive/html/bug-coreutils/2006-07/msg00044.html
  # https://stackoverflow.com/questions/18700455/string-trimming-using-linux-cut-respecting-utf8-bondaries
  
  if is_wayland_session && command -v wl-paste >/dev/null 2>&1; then
    fullPath=$(copyFromClipboardWayland "$currentDate")
  else
    fullPath=$(copyFromClipboardX11 "$currentDate")
  fi

  (( $? )) && showException "Save clipboard error"
  echo "$fullPath";
}

# Publish file and copy link to international (*.com) or local (*.ru) location zone. RU link is shortened by default
# $1 String: file path to publish
# $2 Boolean: copy international link ?
function publishWithComZone() {
  local publishPath=$( yandex-disk publish "$1" )

  if [[ "$publishPath" = "unknown publish error"* || "$publishPath" = "unknown error"* || "$publishPath" = "Error:"* ]]; then
    showException "<b>$publishPath</b>" "$publishPath"
  fi
  local comLink="https://disk.yandex.com${publishPath#*.sk}"

  echo "$1"
  if (( $2 )); then
    echo "$publishPath"
    if is_wayland_session && command -v wl-copy >/dev/null 2>&1; then
      printf '%s' "$comLink" | wl-copy
    else
      echo "$comLink" | xclip -filter -selection clipboard
    fi
  else
    if is_wayland_session && command -v wl-copy >/dev/null 2>&1; then
      printf '%s' "$publishPath" | wl-copy
    else
      echo "$publishPath" | xclip -filter -selection clipboard
    fi
    echo "$comLink"
  fi

  showLongMsg "Public link to the $1 is copied to the clipboard. \n <a href='$comLink'><b>$comLink</b></a> \n <a href='$publishPath'><b>$publishPath</b></a>"
}

# Unpublish file and its copies from the stream directory. 
# If file is outside of the root directory in sync, the function will try to find it in the stream directory
# $1 String: directory without fileName where copies are located
# $2 String: the main file for finding dublicates
function unpublishCopyList() {
  local baseDir=$1
  local nextFile=$2
  local nextFileName=$fileName
  
  local index=0
  local indexPart=''
  local unpublishRes=''
  local res=''
  while [ -f "$nextFile" ]; do
    res=$( yandex-disk unpublish "$nextFile" )
    unpublishRes+="<b>$nextFileName</b> - $res; \n"
    
    ((++index));
    indexPart="_$index"
    nextFileName="$fileNamePart$indexPart$extPart"
    nextFile="$baseDir/$nextFileName"

#     waitForReady;
  done

  echo "$unpublishRes"
  if [[ "$unpublishRes" = "unknown error"* || "$unpublishRes" = "Error:"* ]]; then
    (( isBatchError )) && exit 1;
  fi
}


waitForReady


# Rename file if already exist in the destination and temporal directories
isFileNameChanged=0;
if [[ ( -f "$streamFilePath" || -f "$yaDiskFilePath" ) && ( ( $isOutsideFile = 1 && $commandType = "PublishToYandex"* ) || $commandType = "File"* ) ]]; then
  index=0
  indexPart=''
  srcFilePath=''
  while [ -f "$streamFilePath" ] || [ -f "$yaDiskFilePath" ] || [ -f "$srcFilePath" ]; do
    ((++index))
    indexPart="_$index"
    fileName="$fileNamePart$indexPart$extPart"
    yaDiskFilePath="$yaDisk/$fileName"
    streamFilePath="$streamDir/$fileName"
    srcFilePath="$filePath/$fileName"
  done

  mv "$F" "$srcFilePath"
  isFileNameChanged=1
#   kdialog --passivepopup "$fileName $yaDiskFilePath \n $streamFilePath " 15;
fi
# elif [[ "$streamFilePath" != $F && "$yaDiskFilePath" = $F ]]; then
#   "yaDiskFilePath = srcFilePath. \n <b>Skip for now, mv and cp inside ya disk directory is unstabled</b>: \nit leads to sync process hangs and broken public links, if combined with publish."


# Publish actions
if [[ $commandType = 'PublishToYandexCom' || $commandType = 'PublishToYandex' ]]; then
  isComLink=1
  if [ $commandType = 'PublishToYandex' ]; then
    isComLink=0
  fi
  
  publishWithComZone "$srcFilePath" $isComLink
  (( isOutsideFile )) && mv "$yaDiskFilePath" $streamDir
elif [[ $commandType = 'ClipboardPublishToCom' || $commandType = 'ClipboardPublish' ]]; then 
  clipDestPath=$(copyFromClipboard)
  (( $? )) && exit 1

  status=$(yandex-disk sync)
  echo "$status - $clipDestPath"
  showMsg "Clipboard flushed to stream: \n <b>$clipDestPath</b> \n $status" 5
  
  isComLink=1
  if [ $commandType = 'ClipboardPublish' ]; then
    isComLink=0
  fi

  waitForReady;
  publishWithComZone "$clipDestPath" $isComLink


# Unpublish actions
elif [ $commandType = 'UnpublishFromYandex' ]; then
  unpublishRes=''
  if (( isOutsideFile )); then
    unpublishRes=$( yandex-disk unpublish "$streamFilePath" )
  else
    unpublishRes=$( yandex-disk unpublish "$srcFilePath" )
  fi

  if [[ "$unpublishRes" = "unknown error"* || "$unpublishRes" = "Error:"* ]]; then
    showException "$unpublishRes for <b>$fileName</b>." "$unpublishRes - $fileName"
  fi

  echo "$unpublishRes - $fileName"
  showMsg "$unpublishRes for <b>$fileName</b>." 5
elif [ $commandType = 'UnpublishAllCopy' ]; then
  unpublishRes=''
  if (( isOutsideFile )); then
    unpublishRes=$( unpublishCopyList "$streamDir" "$streamFilePath" )
  else
    unpublishRes=$( unpublishCopyList "$filePath" "$srcFilePath" )
  fi

  status=$?
  timeout=10
  if (( status )); then
    showError "<b>Not all files processed successfully</b>";
    timeout=15
  fi
  showMsg "Files unpublished: \n $unpublishRes" $timeout

  
# Copy & move actions without publishing
elif [ $commandType = 'ClipboardToStream' ]; then
  copyResult=`copyFromClipboard`
  (( $? )) && exit 1

  status=`yandex-disk sync`
  echo "$status - $copyResult"
  showMsg "Clipboard flushed to stream: \n <b>$copyResult</b> \n $status" 10
elif [ $commandType = 'FileAddToStream' ]; then
  cp -rf "$srcFilePath" $streamDir
  (( $? )) && showException "Copy error";
  status=`yandex-disk sync`
  echo "$status - $srcFilePath"
  showMsg "<b>$srcFilePath</b> is copied to the file stream. \n $status" 5;
elif [ $commandType = 'FileMoveToStream' ]; then
  mv -f "$srcFilePath" $streamDir
  (( $? )) && showException "Move error";
  status=`yandex-disk sync`
  echo "$status - $srcFilePath"
  showMsg "<b>$srcFilePath</b> is moved to the file stream. \n $status" 5
else
  workPath="$HOME/.local/share/kservices5/ServiceMenus"
  showMsg "<b>Unknown action $commandType</b>. \n\n Check <a href='file://$workPath/$c'>$workPath/$c</a> for available actions." 15
  echo "Unknown action: $commandType"
fi

renameBack
echo -e "Status: Done $(date '+%Y-%m-%d %H:%M:%S')"
