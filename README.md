# OLAAF-Transient

OLAAF-Transient provides an implementation of the transient authentication. Goal of this type of
authentication is to check if a particular version of a document is authentic or not. The basic
idea behind this implementation is the following:
- Hashes are calculated for each document that should be authenticable and inserted into a database.
Currently, `.html` and `.pdf` formats are supported.
- Hashes of `.html` documents are calculated based on the content of their elements which have `tuf-authenticate` class set. This means that a document will stay authentic even if its style is changed.
Planned improvements include making sure that no parts of the document's authentic content are
actually invisible (e.g. have a `css` class which sets display to `none`).
- The database stores hashes of not just the newest, but also of older versions of the document, as well
as information such as when a version was current.
- A user who wants to be able to check if a document is authentic or not needs to install a browser extension.
Currently supported browsers are `Google Chrome`, `Mozilla Firefox` and `Microsoft Edge`.
- Once a user has installed the extension, they check authenticity of the currently displayed document simply
by invoking clicking on the extension.
- The extension sends content of the document to a web server, which then calculates its hash and compares it
with that document's hashes stored in the database. Documents are identified by their paths e.g. `us/ca/cities/san-mateo/ordinances/2019/7`. The server then returns one of the following replies:
  - The document is authentic and current, followed by the date when the document became valid.
  - The document is authentic but not current, followed by the date range when the document was valid.
  - Not authentic, meaning that none of the document's hashes loaded into the database match the provided one.
  - Cannot authenticate, meaning that that document is not familiar to the system (its hashes haven't been loaded into the database).

This implementation assumes that all documents are stored in a git repository. That means that the historical
versions of those documents can be accessed easily. When inserting the hashes into the database, all commits of
the repository are traversed, starting with the one first one which was not previously processed and stored in
the database.

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
