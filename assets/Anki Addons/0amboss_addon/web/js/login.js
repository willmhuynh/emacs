/*
AMBOSS Anki Add-on

Copyright (C) 2019 AMBOSS MD Inc. <https://www.amboss.com/us>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version, with the additions
listed at the end of the license file that accompanied this program.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

const form = document.getElementById("amboss-login-form");
const user = document.getElementById("inputEmail");
const pass = document.getElementById("inputPassword");
const notification = document.getElementById("notification");
const welcome = document.getElementById("welcome");
const params = new URL(window.location).searchParams;
const context = {
  app: {
    name: "anki-addon",
    version: params.get("addonVersion") || "unknown",
    hostVersion: params.get("ankiVersion") || "unknown"
  }
};

function setupLoginHandler(graphQlUri) {
  form.addEventListener("submit", function() {
    login(event, graphQlUri);
  });
}

function login(event, graphQlUri) {
  const graph = graphql(graphQlUri, {
    asJSON: true,
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    }
  });
  const login = graph
    .mutate(
      `{
            login(login: "${user.value}", password: "${pass.value}", deviceId: "anki") {
                token
                user {
                  eid
                  firstName
                }
               }
            }`
    )()
    .then(function(response) {
      const token = response.login.token;
      const firstName = response.login.user.firstName;
      const userId = response.login.user.eid;
      if (window.analytics) {
        window.analytics.identify(userId);
        window.analytics.track(
          "anki-addon.login.success",
          {},
          { context: context }
        );
      }
      notification.innerHTML = ``;
      form.innerHTML = ``;
      welcome.innerHTML = `
        <div class="amboss-login-welcome">
            <h2>Welcome${firstName ? ", " + firstName : ""}!</h2>
            <div class="amboss-login-welcome-message">Have fun with AMBOSS and Anki!</div>
        </div>`;
      pycmd(`amboss:login:${userId}:${token}`);
      window.setTimeout(function() {
        pycmd("amboss:close");
      }, 2000);
    })
    .catch(function(error) {
      if (window.analytics) {
        window.analytics.track(
          "anki-addon.login.fail",
          { error: error.toString() },
          { context: context }
        );
      }
      notification.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show">
          Looks like you entered the wrong email or password.<br>
          Please try again.
          <button type="button" class="close" data-dismiss="alert">&times;</button>
        </div>`;
      pass.value = "";
    });
  event.preventDefault();
}

function showVersionWarning(versionCheckResult) {
  let warnElm = document.getElementById("version-warning");
  warnElm.innerHTML = `
    <span class="warning">Warning</span>: Your Anki installation is outdated.
    You currently have version ${versionCheckResult.current} installed. For the add-on to work
    best we recommend that you install version <b>${versionCheckResult.minimum}</b> or later. Earlier releases
    might not work properly and cause unexpected issues. You can get the latest official
    Anki release for your platform <b><a href="https://apps.ankiweb.net#download">here</a></b>.
  `;
  warnElm.classList.add("visible");
}

const forgot = () => {
  pycmd(
    `https://www.amboss.com/us/account/forgotPassword?preset_email=${encodeURIComponent(
      user.value
    )}`
  );
};

const signup = () => {
  aid = "";
  if (window.analytics) {
    window.analytics.track(
      "anki-addon.login.register",
      {},
      { context: context }
    );
    try {
      aid = window.analytics.user().anonymousId();
    } catch (e) {}
  }
  pycmd(
    `https://www.amboss.com/us/account/register?utm_campaign=anki&utm_source=anki_login&utm_medium=anki&preset_email=${encodeURIComponent(
      user.value
    )}` + (aid ? `&utm_term=${aid}` : ``)
  );
};
