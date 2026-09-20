[out:json][timeout:60];
(
  nwr["amenity"~"hospital|clinic|doctors"](24.4,90.95,25.2,91.75);
  nwr["healthcare"~"hospital|clinic|centre"](24.4,90.95,25.2,91.75);
);
out center tags;
