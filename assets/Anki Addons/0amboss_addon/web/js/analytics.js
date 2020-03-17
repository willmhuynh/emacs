// disable cookies
document.__defineGetter__("cookie", function() {
  return "";
});

!(function() {
  const analytics = (window.analytics = window.analytics || []);
  if (!analytics.initialize)
    if (analytics.invoked)
      window.console &&
        console.error &&
        console.error("analytics snippet included twice");
    else {
      analytics.invoked = !0;
      analytics.methods = [
        "setAnonymousId",
        "identify",
        "track",
        "page",
      ];
      analytics.factory = function(t) {
        return function() {
          const e = Array.prototype.slice.call(arguments);
          e.unshift(t);
          analytics.push(e);
          return analytics;
        };
      };
      for (let t = 0; t < analytics.methods.length; t++) {
        const e = analytics.methods[t];
        analytics[e] = analytics.factory(e);
      }
      analytics.load = function(t, e) {
        const n = document.createElement("script");
        n.type = "text/javascript";
        n.async = !0;
        // TODO: inject
        n.src = "https://www.amboss.com/us/api/sprx/cdn/" + t + "/a.min.js";
        const a = document.getElementsByTagName("script")[0];
        a.parentNode.insertBefore(n, a);
        analytics._loadOptions = e;
      };
      analytics.SNIPPET_VERSION = "4.1.0";
      // TODO: inject
      analytics.load("JabXayKea69oVRQrDghBRiGJ3g7pdHdP");
    }
})();
