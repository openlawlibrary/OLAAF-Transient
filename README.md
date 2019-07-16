# OLAAF-Transient

Implementation of transient authentication

## Requirements

Download web driver for Chrome: https://sites.google.com/a/chromium.org/chromedriver/downloads
Include the Chrome driver location in the path environment variable. Make sure that
`chromedriver.exe` version matches version of the installed `Google Chrome` browser.

## Quick setup

In order to install the package, activate virtual env if any and from this dir run
`pip install -e .` .

### Run hashes synchronization

In order to run synchronization of hashes, run the following:
`python manage.py synchashes E:\library\law-html`

### Run local server

Navigate to `OLAAF-Transient` and run `python manage.py runserver` in order to start the local server.

### Extensions setup

Once hashes are stored to database, then it's required to install extensions so that
hashes can be verified.

#### Chrome setup

Go to `chrome://extensions/` and click to `Load unpacked`, navigate to:
`open-law-authentication\extensions\chrome-extension` and select dir.

#### Firefox setup

Go to `about:debugging#addons` and click to `Load Temporary Add-on` and then
select `open-law-authentication\extensions\firefox-extension\authenticate.js`.

#### Edge setup

Open Microsoft Edge and type 'about:flags' into the address bar.
Select the Enable extension developer features checkbox. ...
Select More (...) ...
Select Extensions from the menu.
Select the Load extension button.
Navigate to `open-law-authentication\extensions\edge-extension` and select dir.
