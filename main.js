import mapboxgl from 'mapbox-gl';
import WindLayer from '@jindin/mapbox-gl-wind-layer';
import 'mapbox-gl/dist/mapbox-gl.css';

mapboxgl.accessToken = 'TOKEN';

const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/dark-v11',
  center: [69.3451, 30.3753],
  zoom: 4.5,
  projection: 'mercator'
});
const jsonFiles = [
  'gfs_20240725_00.json',
  'gfs_20240724_00.json',
  'gfs_20240723_00.json'
];

const getLatestJsonFile = () => {
  jsonFiles.sort((a, b) => {
    const dateA = a.match(/(\d{4})(\d{2})(\d{2})/);
    const dateB = b.match(/(\d{4})(\d{2})(\d{2})/);

    if (!dateA || !dateB) return 0;

    return new Date(dateB[0]) - new Date(dateA[0]);
  });

  return jsonFiles[0];
};

map.on('load', async () => {
  // Add National Boundary Layer
  map.addSource("nationalBoundary", {
    type: "vector",
    scheme: "tms",
    tiles: ["http://172.18.1.178:8080/geoserver/gwc/service/tms/1.0.0/abdul_sattar:National_Boundary@EPSG:900913@pbf/{z}/{x}/{y}.pbf"],
  });

  map.addLayer({
    id: "nationalBoundary",
    type: "line",
    source: "nationalBoundary",
    "source-layer": "National_Boundary",
    layout: {
      visibility: 'visible'
    },
    paint: {
      "line-opacity": 0.8,
      "line-color": "yellow",
      "line-width": 2,
    }
  });

  // Fetch the latest JSON file
  const latestJsonFile = getLatestJsonFile();
  if (latestJsonFile) {
    fetch(`/json/${latestJsonFile}`)
      .then(response => response.json())
      .then(data => {
        const windLayer = new WindLayer({
          id: 'wind-layer',
          name: 'Wind field layer',
          data: data,
          windyOptions: {
            lineWidth: 1,
            minVelocity: 0,
            maxVelocity: 6,
            particleAge: 90,
            particleMultiplier: 1 / 100,
            opacity: 0.97,
            colorScale: [
              "rgb(255,165,0)",  // Orange
              "rgb(255,215,0)",  // Gold
              "rgb(255,255,0)",  // Bright Yellow
              "rgb(255,255,51)", // Yellow
              "rgb(255,255,102)",// Light Yellow (even more intense)
              "rgb(255,255,178)",// Light Yellow (more intense)
              "rgb(255,255,224)",// Light Yellow
              "rgb(248,248,255)",// Ghost White
              "rgb(240,248,255)",// Alice Blue
              "rgb(173,216,230)",// Light Blue
              "rgb(135,206,250)",// Light Sky Blue
              "rgb(0,191,255)",  // Deep Sky Blue
              "rgb(0,204,255)",  // Lighter Blue
              "rgb(0,153,255)",  // Light Blue
              "rgb(0,102,255)"   // Lighter Dark Blue
              // 'purple',
              // 'red',
              // 'yellow',
              // 'green',
              // 'blue'

            ],
            frameRate: 30, // less framerate is equal to more particles loaded per frame
            maxAge: 60,    // age of particles
            globalAlpha: 0.95, // particles because smaller in size for less value; default was 0.9; it breaks closeup above 1
            velocityScale: 0.01, // Make particles go fast; default value was 0.01
            paths: 7000
          }
        });

        // Add WindLayer to the map
        map.addLayer(windLayer);
      })
      .catch(error => {
        console.error('Error loading wind data:', error);
      });
  }
});
