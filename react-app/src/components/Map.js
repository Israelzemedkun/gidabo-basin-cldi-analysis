import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';

const RISK_COLORS = {
  none: '#888888',
  low: '#27ae60',
  moderate: '#f39c12',
  high: '#e74c3c',
  severe: '#7b0000',
};

const LEGEND_ITEMS = [
  { color: RISK_COLORS.low, label: 'Low risk (<5 t/ha/yr)' },
  { color: RISK_COLORS.moderate, label: 'Moderate (5–15)' },
  { color: RISK_COLORS.high, label: 'High (15–50)' },
  { color: RISK_COLORS.severe, label: 'Severe (>50)' },
];

// Ray-casting point-in-polygon for a leaflet polygon ring
function pointInPolygon(lat, lon, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i].lng, yi = ring[i].lat;
    const xj = ring[j].lng, yj = ring[j].lat;
    const intersect =
      (yi > lat) !== (yj > lat) &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function findNearestPoint(points, lat, lon) {
  let best = null;
  let bestDist = Infinity;
  for (const pt of points) {
    const d = Math.sqrt((pt.lat - lat) ** 2 + (pt.lon - lon) ** 2);
    if (d < bestDist) { bestDist = d; best = pt; }
  }
  return { point: best, dist: bestDist };
}

function ClickHandler({ onLocationSelect, isDrawingRef }) {
  useMapEvents({
    click(e) {
      // Suppress clicks that are actually leaflet-draw vertex placements
      if (isDrawingRef.current) return;
      onLocationSelect({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
  });
  return null;
}

// Compute averaged satellite values across ALL polygons in a slot's ID set.
// Grid points are deduplicated — a point inside multiple overlapping polygons is counted once.
function computeAvgFromSlot(ids, drawnItems, gridPoints) {
  if (!ids || ids.size === 0) return null;

  const seenIdx   = new Set();
  const allInside = [];
  const centers   = [];
  let validLayers = 0;

  for (const id of ids) {
    const layer = drawnItems.getLayer(id);
    if (!layer) continue;
    validLayers++;
    centers.push(layer.getBounds().getCenter());
    const bounds = layer.getBounds();

    if (layer instanceof L.Rectangle) {
      for (let i = 0; i < gridPoints.length; i++) {
        if (seenIdx.has(i)) continue;
        const pt = gridPoints[i];
        if (bounds.contains([pt.lat, pt.lon])) { seenIdx.add(i); allInside.push(pt); }
      }
    } else {
      const raw  = layer.getLatLngs();
      const ring = Array.isArray(raw[0]) ? raw[0] : raw;
      for (let i = 0; i < gridPoints.length; i++) {
        if (seenIdx.has(i)) continue;
        const pt = gridPoints[i];
        if (pointInPolygon(pt.lat, pt.lon, ring)) { seenIdx.add(i); allInside.push(pt); }
      }
    }
  }

  if (validLayers === 0) return null;

  // Pin centroid = average of each polygon's bounds centre.
  const avgLat = centers.reduce((s, c) => s + c.lat, 0) / centers.length;
  const avgLng = centers.reduce((s, c) => s + c.lng, 0) / centers.length;

  let inside = allInside;
  if (inside.length < 2) {
    const { point } = findNearestPoint(gridPoints, avgLat, avgLng);
    if (point) inside = [point];
  }

  if (inside.length === 0) return null;

  const n = inside.length;
  return {
    center: { lat: avgLat, lng: avgLng },
    avg: {
      rainfall:     inside.reduce((s, p) => s + p.rainfall, 0) / n,
      slope:        inside.reduce((s, p) => s + p.slope, 0) / n,
      ndvi:         inside.reduce((s, p) => s + p.ndvi, 0) / n,
      soil_k:       inside.reduce((s, p) => s + p.soil_k, 0) / n,
      pointCount:   n,
      polygonCount: validLayers,
    },
  };
}

// Leaflet-draw polygon/rectangle toolbar
function DrawControl({
  gridPoints,
  onLocationSelect,
  onComparisonSelect,
  comparisonMode,
  isDrawingRef,
  selectedLocation,
  comparisonLocation,
  onDeleteA,
  onDeleteB,
}) {
  const map = useMap();

  // Refs for all callbacks and mode — updated each render, never in effect deps.
  const comparisonModeRef     = useRef(comparisonMode);
  const onComparisonSelectRef = useRef(onComparisonSelect);
  const onLocationSelectRef   = useRef(onLocationSelect);
  const onDeleteARef          = useRef(onDeleteA);
  const onDeleteBRef          = useRef(onDeleteB);
  useEffect(() => { comparisonModeRef.current     = comparisonMode;     }, [comparisonMode]);
  useEffect(() => { onComparisonSelectRef.current = onComparisonSelect; }, [onComparisonSelect]);
  useEffect(() => { onLocationSelectRef.current   = onLocationSelect;   }, [onLocationSelect]);
  useEffect(() => { onDeleteARef.current          = onDeleteA;          }, [onDeleteA]);
  useEffect(() => { onDeleteBRef.current          = onDeleteB;          }, [onDeleteB]);

  // Each slot holds a Set of _leaflet_ids for all its drawn polygon layers.
  const drawnLayerAIdsRef = useRef(new Set());
  const drawnLayerBIdsRef = useRef(new Set());
  // The FeatureGroup shared with the edit control — reachable from cleanup effects.
  const drawnItemsRef     = useRef(null);

  // When Location A is not a polygon location (null or direct click), clear all A polygons.
  useEffect(() => {
    if (!selectedLocation || !selectedLocation.polygonData) {
      if (drawnItemsRef.current) {
        for (const id of drawnLayerAIdsRef.current) {
          const layer = drawnItemsRef.current.getLayer(id);
          if (layer) drawnItemsRef.current.removeLayer(layer);
        }
        drawnLayerAIdsRef.current = new Set();
      }
    }
  }, [selectedLocation]);

  // When comparison is cleared (comparisonLocation → null), remove all B polygons.
  useEffect(() => {
    if (!comparisonLocation) {
      if (drawnItemsRef.current) {
        for (const id of drawnLayerBIdsRef.current) {
          const layer = drawnItemsRef.current.getLayer(id);
          if (layer) drawnItemsRef.current.removeLayer(layer);
        }
        drawnLayerBIdsRef.current = new Set();
      }
    }
  }, [comparisonLocation]);

  // Main draw-control setup — runs once per gridPoints load, never mid-drawing.
  useEffect(() => {
    if (!gridPoints || !gridPoints.length) return;

    // drawnItems is the FeatureGroup the edit control operates on.
    // All drawn polygon layers live here so edit/delete buttons work correctly.
    const drawnItems = new L.FeatureGroup();
    drawnItemsRef.current = drawnItems;
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      position: 'topleft',
      draw: {
        polygon:      { shapeOptions: { color: '#3b82f6', fillOpacity: 0.15 } },
        rectangle:    { shapeOptions: { color: '#3b82f6', fillOpacity: 0.15 } },
        polyline:     false,
        circle:       false,
        circlemarker: false,
        marker:       false,
      },
      edit: { featureGroup: drawnItems },
    });
    map.addControl(drawControl);

    // Track draw-in-progress so ClickHandler can suppress vertex clicks.
    function onDrawStart() { isDrawingRef.current = true; }
    function onDrawStop()  { isDrawingRef.current = false; }

    function onCreated(e) {
      if (e.layerType !== 'polygon' && e.layerType !== 'rectangle') return;

      const isComparison = comparisonModeRef.current;
      const ids = isComparison ? drawnLayerBIdsRef.current : drawnLayerAIdsRef.current;

      // Add the new layer to drawnItems (visible + editable) and record its ID.
      drawnItems.addLayer(e.layer);
      ids.add(e.layer._leaflet_id);

      const result = computeAvgFromSlot(ids, drawnItems, gridPoints);
      if (!result) return;

      const loc = { lat: result.center.lat, lon: result.center.lng, polygonData: result.avg };
      if (isComparison) {
        onComparisonSelectRef.current(loc);
      } else {
        onLocationSelectRef.current(loc);
      }
    }

    function onEdited(e) {
      // Track which slots had layers edited so we recompute each affected slot once.
      let needsUpdateA = false;
      let needsUpdateB = false;

      e.layers.eachLayer(layer => {
        const id = layer._leaflet_id;
        if (drawnLayerAIdsRef.current.has(id)) needsUpdateA = true;
        if (drawnLayerBIdsRef.current.has(id)) needsUpdateB = true;
      });

      if (needsUpdateA) {
        const result = computeAvgFromSlot(drawnLayerAIdsRef.current, drawnItems, gridPoints);
        if (result) {
          onLocationSelectRef.current({ lat: result.center.lat, lon: result.center.lng, polygonData: result.avg });
        }
      }
      if (needsUpdateB) {
        const result = computeAvgFromSlot(drawnLayerBIdsRef.current, drawnItems, gridPoints);
        if (result) {
          onComparisonSelectRef.current({ lat: result.center.lat, lon: result.center.lng, polygonData: result.avg });
        }
      }
    }

    function onDeleted(e) {
      let needsUpdateA = false;
      let needsUpdateB = false;

      e.layers.eachLayer(layer => {
        const id = layer._leaflet_id;
        if (drawnLayerAIdsRef.current.has(id)) {
          drawnLayerAIdsRef.current.delete(id);
          needsUpdateA = true;
        } else if (drawnLayerBIdsRef.current.has(id)) {
          drawnLayerBIdsRef.current.delete(id);
          needsUpdateB = true;
        }
      });

      if (needsUpdateA) {
        if (drawnLayerAIdsRef.current.size === 0) {
          onDeleteARef.current();
        } else {
          const result = computeAvgFromSlot(drawnLayerAIdsRef.current, drawnItems, gridPoints);
          if (result) {
            onLocationSelectRef.current({ lat: result.center.lat, lon: result.center.lng, polygonData: result.avg });
          }
        }
      }
      if (needsUpdateB) {
        if (drawnLayerBIdsRef.current.size === 0) {
          onDeleteBRef.current();
        } else {
          const result = computeAvgFromSlot(drawnLayerBIdsRef.current, drawnItems, gridPoints);
          if (result) {
            onComparisonSelectRef.current({ lat: result.center.lat, lon: result.center.lng, polygonData: result.avg });
          }
        }
      }
    }

    map.on(L.Draw.Event.DRAWSTART, onDrawStart);
    map.on(L.Draw.Event.DRAWSTOP,  onDrawStop);
    map.on(L.Draw.Event.CREATED,   onCreated);
    map.on(L.Draw.Event.EDITED,    onEdited);
    map.on(L.Draw.Event.DELETED,   onDeleted);

    return () => {
      map.off(L.Draw.Event.DRAWSTART, onDrawStart);
      map.off(L.Draw.Event.DRAWSTOP,  onDrawStop);
      map.off(L.Draw.Event.CREATED,   onCreated);
      map.off(L.Draw.Event.EDITED,    onEdited);
      map.off(L.Draw.Event.DELETED,   onDeleted);
      map.removeControl(drawControl);
      map.removeLayer(drawnItems);
      drawnItemsRef.current     = null;
      drawnLayerAIdsRef.current = new Set();
      drawnLayerBIdsRef.current = new Set();
      isDrawingRef.current      = false;
    };
  }, [map, gridPoints]); // intentionally excludes callbacks — all read via refs

  return null;
}

function Legend() {
  return (
    <div className="map-legend">
      <div className="legend-title">Erosion Risk</div>
      {LEGEND_ITEMS.map(({ color, label }) => (
        <div key={label} className="legend-item">
          <span className="legend-dot" style={{ background: color }} />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

export default function Map({
  selectedLocation,
  onLocationSelect,
  onComparisonSelect,
  onDeleteA,
  onDeleteB,
  riskLevel,
  comparisonMode,
  comparisonLocation,
  comparisonRiskLevel,
  gridPoints,
}) {
  // Shared ref: DrawControl sets true on draw:drawstart, false on draw:drawstop.
  // ClickHandler reads it to suppress map clicks that are actually vertex placements.
  const isDrawingRef = useRef(false);

  const pinColor = RISK_COLORS[riskLevel] || RISK_COLORS.none;
  const compPinColor = RISK_COLORS[comparisonRiskLevel] || '#3b82f6';

  let instructionText = null;
  if (comparisonMode) {
    instructionText = 'Click to place comparison pin';
  } else if (!selectedLocation) {
    instructionText = 'Click anywhere in Ethiopia to assess erosion risk';
  }

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <MapContainer
        center={[9.0, 40.0]}
        zoom={6}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickHandler onLocationSelect={onLocationSelect} isDrawingRef={isDrawingRef} />
        {gridPoints && (
          <DrawControl
            gridPoints={gridPoints}
            onLocationSelect={onLocationSelect}
            onComparisonSelect={onComparisonSelect}
            comparisonMode={comparisonMode}
            isDrawingRef={isDrawingRef}
            selectedLocation={selectedLocation}
            comparisonLocation={comparisonLocation}
            onDeleteA={onDeleteA}
            onDeleteB={onDeleteB}
          />
        )}

        {/* Primary location pin (Improvement 1) */}
        {selectedLocation && (
          <CircleMarker
            center={[selectedLocation.lat, selectedLocation.lon]}
            radius={14}
            fillColor={pinColor}
            fillOpacity={0.9}
            weight={2}
            color="white"
            className="pin-pulse"
          />
        )}

        {/* Comparison pin — blue (Improvement 5) */}
        {comparisonLocation && (
          <CircleMarker
            center={[comparisonLocation.lat, comparisonLocation.lon]}
            radius={14}
            fillColor={compPinColor}
            fillOpacity={0.9}
            weight={2}
            color="white"
            className="pin-pulse pin-pulse--b"
          />
        )}
      </MapContainer>

      {instructionText && (
        <div
          className={
            'map-instruction-overlay' +
            (comparisonMode ? ' map-instruction-overlay--compare' : '')
          }
        >
          {instructionText}
        </div>
      )}

      <Legend />
    </div>
  );
}
