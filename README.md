#  xlwings Server: Azure AD auth for Desktop Excel

This sample repo shows you how you can authenticate and authorize users of xlwings Server via Azure AD.
For more info about xlwings Server, see the [docs](https://docs.xlwings.org/en/latest/remote_interpreter.html).

## Supported spreadsheets by this repo

* Desktop Excel on Windows
* Desktop Excel on macOS

Every version of Excel is supported, it doesn't have to be Microsoft 365.

## 1. Azure AD setup

* On [Microsoft Azure](https://portal.azure.com), go to `All Services` > `Azure Active Directory`

* Under `App registrations` (left sidebar), click on `New registration` button at top
   * `Name`: something like `xlwings`
   * `Supported account types`: for an internal application, this is `Accounts in this organizational directory only (Single tenant)`
   * `Redirect URI`: Select `Public client/native (mobile & desktop)` in the dropdown and provide the following as URL: `http://localhost`
   * Then click on `Register` at the bottom

* Under `Expose an API` (left sidebar):
   * Click on `Add a scope`
   * If there are no existing scopes, you need to first accept the default Application ID URI (something like `api://...`)
   * `Save and continue`
   * Then fill in the scope definition:
      * `Scope name`: add something like `default`
      * `Who can consent`: `Admins and users`
      * `Admin consent display name`: `xlwings needs access to Azure AD`
      * `Admin consent description`: `Allow xlwings to authenticate via Azure AD`
      * => Use same values for User consent
      * `State`: `enabled`
      * Confirm with `Add scope`

* Under `API permissions` (left sidebar): 
   * Reload the browser page to make sure your previously created application (`xlwings`) shows up
   * Delete the existing `Microsoft Graph > User.Read` permission (`...` > `Remove permission`)
   * Click on `Add a permission`
      * Select the tab `My APIs`
      * Select the previously created application `xlwings`
      * Activate the checkbox under `Permissions` for `default`
      * Confirm with `Add permissions`

* Under `Overview` (left sidebar):
   * Copy Application (client) ID
   * Copy Directory (tenent) ID
   * Under `Expose an API`, copy the previously defined `Scope` (`api://...`)
   * Add them to your `xlwings.conf` file (check location [here](https://docs.xlwings.org/en/latest/addin.html#user-config-ribbon-config-file)) (including quotes):

     ```
     "AZUREAD_TENANT_ID","xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
     "AZUREAD_CLIENT_ID","xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
     "AZUREAD_SCOPES","api://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/default"
     ```
      
[OPTIONAL] RBAC: Role-based access control (only required for `hello3` sample)

* `App roles` (left sidebar):
   * Click on `Create app role`
   * `Display name`: `Writer`
   * `Allowed member types`: `Users/Groups`
   * `Value`: `Task.Write`
   * `Description`: `Writer`
   * Checkbox must be active for `Do you want to enable this app role?`
   * `Apply`
   => Repeat this step to create a `Reader` role (use `Task.Read` as the `Value`)

* Go all the way back to `All Services` > `Azure Active Directory`, then under `Enterprise applications` (left sidebar):
   * Select the previously created application `xlwings`
   * Click on `1. Assign users and groups`
   * Click on `Add user/group`
      * Under `User`, click on `None Selected` and select a user or group. Confirm with `Select`.
      * Under `Role`, click on `None Selected` and select `Writer` or `Reader` (if you don't see any role, wait a moment and reload the page). Confirm with `Select`.
      * Repeat the last step to give the user both `Reader` and `Writer` roles

## 2. xlwings Server

Follow these steps to run the backend server locally.

### Environment variables

* Run `cp .env.template .env`
* Then edit the `.env` file and provide the required values

### Option a) Use a local Python installation

* Create a virtual environment and run `pip install -r requirements.txt`
* Run the server via `python run.py`

### Option b) Use Docker

* Run `docker compose up`

## 3. Excel file

Note that this Excel file uses the *standalone* mode, i.e., comes with all the required VBA code and is not dependent on the xlwings add-in.

* Currently, you'll need a local Python installation with xlwings and the optional dependency `msal` (`pip install msal`)
* Open `demo.xlsm` and click the buttons: they correspond to the endpoints under `app/api.py`.
* The very first time you click a button, you'll need to login and accept the consent screen.
* Access tokens are cached and remain valid for 60-75 minutes. If an access token is expired, it will be automatically renewed, which will slow down that request. Subsequent requests will then again use the cached token.
* The demo file uses the following code to call an endpoint with the token in the `Authorization` header:

  ```vb.net
  Sub Hello1()
    RunRemotePython "http://127.0.0.1:8000/hello1", auth:="Bearer " & GetAzureAdAccessToken()
  End Sub
  ```

## xlwings.conf: optional settings

* If you're logged into multiple Microsoft accounts, you can add the following line to the `xlwings.conf` file to select a specific account:

  ```
  "AZUREAD_USERNAME","your@email.com"
  ```

* If you need to change the random port of the login flow (under `http://localhost`) to a dedicated port, you can provide it like so:

  ```
  "AZUREAD_PORT","9999"
  ```

## Reset authentication

* If you assign a new role to a user, they will have to reset the access token (or wait until it expires).
* You can either run the following on a command prompt: ``xlwings auth azuread --reset``
* Or call this functionality from VBA like so:

  ```vb.net
  Sub Reset()
      RunPython "from xlwings import cli;cli._auth_aad(reset=True)"
  End Sub
  ```