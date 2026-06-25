const Sentry = require("@sentry/node");

Sentry.init({
  dsn: "https://7d66de414bfd97192d3e04ea79d47849@o4510589573660672.ingest.us.sentry.io/4510589605314560",
  dataCollection: {
    // userInfo: false,
    // httpBodies: [],
  },
});
