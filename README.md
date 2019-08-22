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
by  clicking on the extension.
- The extension sends content of the document to a web server, which then calculates its hash and compares it
with that document's hashes stored in the database. Documents are identified by their paths e.g. `us/ca/cities/san-mateo/ordinances/2019/7`. The server then returns one of the following replies:
  - The document is authentic and current, followed by the date when the document became valid.
  - The document is authentic but not current, followed by the date range when the document was valid.
  - Not authentic, meaning that none of the document's hashes loaded into the database match the provided one.
  - Cannot authenticate, meaning that document is not the system does not recognize that document (its hashes haven't been loaded into the database).

This implementation assumes that all documents are stored in a git repository. That means that the historical
versions of those documents can be accessed easily. When inserting hashes into the database, all commits of
the repository are traversed, starting with the one first one which was not previously processed and added to
the database. Synchronization of hashes can be invoked manually, by calling the `synchashes` command.
Additionally, this project includes a git hook, which can be added to a the `.git/hooks` directory of the
repository containing authenticable documents. This hook is invoked after `git pull` is successfully executed
and processes all new commits.

## Requirements

In order to be able to insert hashes into the database, it is necessary to install Google Chrome and
download web driver for this browser. The we driver can be found (here)[https://sites.google.com/a/chromium.org/chromedriver/downloads].
Once downloaded, include the Chrome driver in the path environment variable.
Make sure that `chromedriver.exe` version matches the version of the installed `Google Chrome` browser.
At the moment, SQLite is the only supported database. This will be updated in the future.

## Quick setup

In order to install the package, activate virtual env if any and from this directory run
`pip install -e .` .

### Run hashes synchronization

In order to run synchronization of hashes, run the following:
`python manage.py synchashes` when inside the project root.

### Git hook

There are two files inside the `git-hooks` directory located directly in the project's root: `post_merge.py` and
`post_merge`. `post_merge` is a git hook which calls `post_merge.py` script. This git hook is invoked after
a commit is merged. This means that it is also invoked after `git pull`. To use this hook, copy it to the
`.git/hooks` directory of the repository containing authenticable documents. Update line 6 of `post_merge`
file and provide path to your local python interpreter. The specified environment must have
 `OLAAF-Transient` installed. Making this modification easier to do is among he planned improvements.

### Run the local server

In order to be able to test authentication of documents, it is necessary to start the local server.
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
