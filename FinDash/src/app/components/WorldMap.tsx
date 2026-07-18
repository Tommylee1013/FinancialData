import React, { useState } from "react";
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from "react-simple-maps";
import { X } from "lucide-react";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface PortMarker {
  id: string;
  name: string;
  city: string;
  country: string;
  coords: [number, number];
  index: string;
  value: number;
  change: number;
  unit: string;
  prev: number;
  date: string;
}

interface FreightMapProps {
  markers: PortMarker[];
}

export function FreightWorldMap({ markers }: FreightMapProps) {
  const [selected, setSelected] = useState<PortMarker | null>(null);

  return (
    <div className="relative w-full bg-card rounded border border-border overflow-hidden">
      <ComposableMap
        projection="geoNaturalEarth1"
        projectionConfig={{ scale: 140 }}
        style={{ width: '100%', height: '360px' }}
      >
        <ZoomableGroup zoom={1}>
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="var(--secondary)"
                  stroke="var(--border)"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { outline: 'none', fill: 'var(--accent)' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>
          {markers.map(m => (
            <Marker key={m.id} coordinates={m.coords} onClick={() => setSelected(m)}>
              <circle
                r={7}
                fill={m.change >= 0 ? '#16A34A' : '#DC2626'}
                fillOpacity={0.9}
                stroke="white"
                strokeWidth={1.5}
                style={{ cursor: 'pointer' }}
              />
              <text
                textAnchor="middle"
                y={-12}
                style={{
                  fontSize: '9px',
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 600,
                  fill: 'var(--foreground)',
                  pointerEvents: 'none',
                }}
              >
                {m.index}
              </text>
            </Marker>
          ))}
        </ZoomableGroup>
      </ComposableMap>

      {selected && (
        <div className="absolute top-3 right-3 bg-card border border-border rounded shadow-lg p-3 w-52 z-10">
          <div className="flex justify-between items-center mb-2">
            <div>
              <div className="text-xs font-bold text-foreground">{selected.city}</div>
              <div className="text-[10px] text-muted-foreground">{selected.country}</div>
            </div>
            <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
              <X size={12} />
            </button>
          </div>
          <div className="border-t border-border pt-2 space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">{selected.index}</span>
              <span className="font-mono font-semibold text-foreground">{selected.value.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Change</span>
              <span className={`font-mono font-semibold ${selected.change >= 0 ? 'text-up' : 'text-down'}`}>
                {selected.change >= 0 ? '+' : ''}{selected.change.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Prev</span>
              <span className="font-mono text-foreground">{selected.prev.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">As of</span>
              <span className="font-mono text-muted-foreground">{selected.date}</span>
            </div>
          </div>
        </div>
      )}

      <div className="absolute bottom-2 left-2 flex items-center gap-3 text-[10px] text-muted-foreground bg-card/80 px-2 py-1 rounded">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-up inline-block" />Rise</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-down inline-block" />Fall</span>
        <span>Click for details</span>
      </div>
    </div>
  );
}

interface CountryData {
  iso: string;
  name: string;
  flag: string;
  cpi: number;
  gdp: number;
  unemploy: number;
  pmi: number;
  rate: number;
  date: string;
  cpiChange: number;
  gdpChange: number;
}

interface MacroMarker {
  country: string;
  coords: [number, number];
}

interface MacroWorldMapProps {
  markers: MacroMarker[];
  countryData: Record<string, CountryData>;
}

export function MacroWorldMap({ markers, countryData }: MacroWorldMapProps) {
  const [selected, setSelected] = useState<CountryData | null>(null);

  return (
    <div className="relative w-full bg-card rounded border border-border overflow-hidden">
      <ComposableMap
        projection="geoNaturalEarth1"
        projectionConfig={{ scale: 140 }}
        style={{ width: '100%', height: '340px' }}
      >
        <ZoomableGroup zoom={1}>
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="var(--secondary)"
                  stroke="var(--border)"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { outline: 'none', fill: 'var(--accent)' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>
          {markers.map(m => {
            const d = countryData[m.country];
            if (!d) return null;
            return (
              <Marker key={m.country} coordinates={m.coords} onClick={() => setSelected(d)}>
                <circle
                  r={8}
                  fill="var(--primary)"
                  fillOpacity={0.85}
                  stroke="white"
                  strokeWidth={1.5}
                  style={{ cursor: 'pointer' }}
                />
                <text
                  textAnchor="middle"
                  y={4}
                  style={{
                    fontSize: '8px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontWeight: 700,
                    fill: 'white',
                    pointerEvents: 'none',
                  }}
                >
                  {d.cpi.toFixed(1)}%
                </text>
              </Marker>
            );
          })}
        </ZoomableGroup>
      </ComposableMap>

      {selected && (
        <div className="absolute top-3 right-3 bg-card border border-border rounded shadow-lg p-3 w-56 z-10">
          <div className="flex justify-between items-center mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-base">{selected.flag}</span>
              <div>
                <div className="text-xs font-bold text-foreground">{selected.name}</div>
                <div className="text-[10px] text-muted-foreground">{selected.date}</div>
              </div>
            </div>
            <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
              <X size={12} />
            </button>
          </div>
          <div className="border-t border-border pt-2 space-y-1">
            {[
              { label: 'CPI YoY', val: selected.cpi, unit: '%', change: selected.cpiChange },
              { label: 'GDP QoQ', val: selected.gdp, unit: '%', change: selected.gdpChange },
              { label: 'Unemployment', val: selected.unemploy, unit: '%', change: null },
              { label: 'PMI', val: selected.pmi, unit: '', change: null },
              { label: 'Policy Rate', val: selected.rate, unit: '%', change: null },
            ].map(row => (
              <div key={row.label} className="flex justify-between text-xs">
                <span className="text-muted-foreground">{row.label}</span>
                <span className="font-mono font-semibold text-foreground">
                  {row.val.toFixed(1)}{row.unit}
                  {row.change !== null && (
                    <span className={`ml-1.5 text-[10px] ${row.change >= 0 ? 'text-up' : 'text-down'}`}>
                      {row.change >= 0 ? '▲' : '▼'}{Math.abs(row.change).toFixed(1)}
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="absolute bottom-2 left-2 text-[10px] text-muted-foreground bg-card/80 px-2 py-1 rounded">
        Circle shows CPI YoY (%) | Click for country details
      </div>
    </div>
  );
}
