# yaDiskDolphinMenu
### Yandex Disk integration for KDE Dolphin sub menu: use yandex cloud directory for sharing clipboard content and files between PC, mobile, people, etc..

Inspired by [yandex disk indicator](https://github.com/slytomcat/yandex-disk-indicator/wiki/Yandex-disk-indicator) context menu options

![Screenshot](https://raw.githubusercontent.com/Miheev/yaDiskDolphinMenu/main/wiki/main-mix.png)

## Features:

Let's assume some directory under yandex cloud selected as **inbox** for **file stream**. It can be used as **destination** **for**: 
- Publish files
- Copy & Move files
- Save & Publish clipboard content (text & images)
- Screenshots captured via default KDE tool like [spectacle](https://apps.kde.org/ru/spectacle/) can be copied to clipboard and then saved to cloud via context menu
- Save clipboard content (without publishing)

**Pros** comparing to standard yd-tools menu items
- More resilient behavior: doesn't fail silently if __yandex-disk__ service busy or unavailable, **wait 30s for idle status** and shows notifications accordingly
- Separate menu group
- **Non-blocking** native **notifications** (kdialog)
- Show published links in notification as **clicable links**
- Show **both published links**: for COM domain (EN language) RU domain (RU language)
- Separate menu options for capturing appropriate link (RU, EN) to clipboard (2 links present in notification anyway)
- Doesn't fail on overwrite: **rename automatically** instead (__%name%\_%number%.%extension% or .%extensionName%\_%number%__)
- **Unpublish** file with its **copies** (if copies created with patterns above)
- **Unpublish file outside** of cloud directories (instead of throwing error, unpublish its copy from the inbox directory)
- **Log output** to parent of yandex disk root directory (__$YA_DISK_ROOT/yaMedia.error.log__) 

**Cons**
- EN localization supported only

**HINT**: Set up and use additional account for file synchronization and 3rd party services to prevent over sync and too broad access rights sharing.  
Set up shared directory access from primary to friendly account for such purpose.


## Requirements
- KDE Linux with Dolphin
- [yandex-disk](https://yandex.com/support/disk-desktop-linux/) daemon installed and running
- icons pack from [yd-tools](https://github.com/slytomcat/yandex-disk-indicator/doc/Yandex-disk-indicator) (after installation should be in /usr/share/yd-tools/icons)
- Mix tools used in script (kdialog, date, xclip, other common tools ..)

Since current scripts created on top of yandex disk indicator, there is a good chance that it installs and set up some not listed dependencies.
I'd rather suggest to install it anyway.


### Tested on
- distributive: KDE Neon 5.21
- KDE: 5.21.4
- Linux core version: 5.4.0-72-generic
- bash: 5.0.17(1)-release (x86_64-pc-linux-gnu)


## Install & Setup
- Install & configure [yandex-disk](https://yandex.com/support/disk-desktop-linux/) and [yd-tools](https://github.com/slytomcat/yandex-disk-indicator/wiki/Yandex-disk-indicator) as described in corresponding docs

### Setup via script
- Download repo to some permanent directory 
- Set up variables inside ``setup.sh`` script as described there
- Run ``setup.sh`` script  
It creates scripts symlinks instead of copies (manual setup example)

### Manual setup
- Download repo to somewhere
- Set up environment variables, simple path without whitespaces expected   
    - $YA_DISK_ROOT path: parent of yandex disk root directory, e.g. __$HOME/Public__ 
    Set global static var (local in .bash_profile and .bashrc doesn't work for me)  
``sudo echo "YA_DISK_ROOT=$HOME/Public" >> /etc/environment``
    - set yandex disk root directory and inbox directory under the root, e.g. __$YA_DISK_ROOT/yaDisk__ and __$YA_DISK_ROOT/yaDisk/fileInbox__ respectively  
     Thus parameters can be found in ``./ydmenu.sh`` under line 23:  __yaDisk__ and __streamDir__
- Run commands inside of repo root
    - make default config backup  
``mv $HOME/.local/share/kservices5/ServiceMenus/ydpublish.desktop $HOME/.local/share/kservices5/ServiceMenus/ydpublish.desktop.bak``
    - copy new desktop menu spec  
``cp ./ydpublish.desktop ~/.local/share/kservices5/ServiceMenus``
    - copy script to local bin dir
``cp ./ydmenu.sh ~/bin``

### Finish setup
- Logout & login
- Now __YaDisk__ menu group should be available as shown on the image
- Enjoy!
- Reconfigure via script or manually if needed
