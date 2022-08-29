const hostname = window && window.location && window.location.hostname;

const PRODUCTION = hostname.includes("geshem");

const IMAGES_BASE_URL = PRODUCTION ? "https://imgs.geshem.space" : "";

const MAPBOX_ACCESS_TOKEN =
  "pk.eyJ1IjoieXV2YWRtIiwiYSI6ImNpcnMxbzBuaTAwZWdoa25oczlzZmkwbHcifQ.UHtLngbKm9O8945pJm23Nw";

const IMAGE_COORDINATES = [
  [31.7503896894, 34.4878044232],
  [37.8574239563, 34.5078463729],
  [37.7157066403, 29.4538271687],
  [31.9347389087, 29.4373462909]
];

module.exports = { IMAGES_BASE_URL, MAPBOX_ACCESS_TOKEN, IMAGE_COORDINATES };
