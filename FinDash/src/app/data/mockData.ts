export function generateTrend(base: number, periods: number, volatility: number, bias = 0) {
  const data: { t: number; date: string; v: number }[] = [];
  let v = base;
  const now = new Date();
  for (let i = 0; i < periods; i++) {
    v += (Math.random() - 0.5 + bias) * volatility;
    const pointDate = new Date(now);
    pointDate.setDate(now.getDate() - (periods - 1 - i));
    data.push({ t: i, date: pointDate.toISOString().slice(0, 10), v: Math.max(0, v) });
  }
  return data;
}

export function generateOHLC(base: number, periods: number, volatility: number, bias = 0) {
  const data: { t: number; open: number; high: number; low: number; close: number; date: string }[] = [];
  let price = base;
  const now = Date.now();
  for (let i = 0; i < periods; i++) {
    const open = price;
    const change = (Math.random() - 0.5 + bias) * volatility;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * Math.abs(volatility) * 0.4;
    const low = Math.min(open, close) - Math.random() * Math.abs(volatility) * 0.4;
    const date = new Date(now - (periods - i) * 86400000 * 7).toISOString().slice(0, 10);
    data.push({ t: i, open, high, low, close, date });
    price = close;
  }
  return data;
}

export const marketIndices = [
  { id: 'sp500', name: 'S&P 500', country: 'US', flag: '🇺🇸', value: 5234.18, change: 43.27, changePct: 0.83, prev: 5190.91, high: 5248.32, low: 5201.45, volume: '3.2B', trend: generateTrend(5000, 30, 40, 0.1) },
  { id: 'nasdaq', name: 'NASDAQ', country: 'US', flag: '🇺🇸', value: 16742.39, change: 185.67, changePct: 1.12, prev: 16556.72, high: 16798.11, low: 16611.23, volume: '5.8B', trend: generateTrend(16000, 30, 120, 0.15) },
  { id: 'dow', name: 'Dow Jones', country: 'US', flag: '🇺🇸', value: 38671.69, change: 162.33, changePct: 0.42, prev: 38509.36, high: 38724.18, low: 38532.45, volume: '0.9B', trend: generateTrend(38000, 30, 180, 0.05) },
  { id: 'kospi', name: 'KOSPI', country: 'KR', flag: '🇰🇷', value: 2743.82, change: -6.32, changePct: -0.23, prev: 2750.14, high: 2758.93, low: 2736.11, volume: '8.2T', trend: generateTrend(2700, 30, 20, -0.02) },
  { id: 'kosdaq', name: 'KOSDAQ', country: 'KR', flag: '🇰🇷', value: 876.54, change: 1.32, changePct: 0.15, prev: 875.22, high: 882.34, low: 871.56, volume: '6.4T', trend: generateTrend(860, 30, 8, 0.02) },
  { id: 'nikkei', name: 'Nikkei 225', country: 'JP', flag: '🇯🇵', value: 38236.07, change: 348.12, changePct: 0.92, prev: 37887.95, high: 38389.45, low: 37934.22, volume: '1.2T', trend: generateTrend(37000, 30, 280, 0.1) },
  { id: 'topix', name: 'TOPIX', country: 'JP', flag: '🇯🇵', value: 2721.45, change: 21.03, changePct: 0.78, prev: 2700.42, high: 2734.88, low: 2706.33, volume: '0.8T', trend: generateTrend(2650, 30, 20, 0.1) },
  { id: 'dax', name: 'DAX', country: 'DE', flag: '🇩🇪', value: 18094.32, change: -56.12, changePct: -0.31, prev: 18150.44, high: 18214.67, low: 18067.23, volume: '2.1B', trend: generateTrend(18000, 30, 130, -0.03) },
  { id: 'ftse', name: 'FTSE 100', country: 'GB', flag: '🇬🇧', value: 7952.15, change: 14.23, changePct: 0.18, prev: 7937.92, high: 7978.34, low: 7921.56, volume: '1.8B', trend: generateTrend(7800, 30, 60, 0.03) },
  { id: 'cac', name: 'CAC 40', country: 'FR', flag: '🇫🇷', value: 7734.49, change: -34.82, changePct: -0.45, prev: 7769.31, high: 7778.92, low: 7712.34, volume: '1.4B', trend: generateTrend(7700, 30, 60, -0.05) },
  { id: 'hsi', name: 'Hang Seng', country: 'HK', flag: '🇭🇰', value: 17234.56, change: 209.45, changePct: 1.23, prev: 17025.11, high: 17312.34, low: 17089.23, volume: '98B', trend: generateTrend(16500, 30, 180, 0.12) },
  { id: 'csi300', name: 'CSI 300', country: 'CN', flag: '🇨🇳', value: 3412.78, change: -23.12, changePct: -0.67, prev: 3435.90, high: 3451.23, low: 3401.45, volume: '432B', trend: generateTrend(3500, 30, 40, -0.08) },
];

export const volatilityIndices = [
  { id: 'vix', name: 'VIX', desc: 'S&P 500 Volatility', value: 13.42, change: -0.87, changePct: -6.09, high: 14.56, low: 13.21, trend: generateTrend(16, 30, 1.2, -0.05) },
  { id: 'vkospi', name: 'VKOSPI', desc: 'KOSPI Volatility', value: 14.82, change: 0.23, changePct: 1.58, high: 15.43, low: 14.61, trend: generateTrend(15, 30, 0.8, 0.01) },
  { id: 'vstoxx', name: 'VSTOXX', desc: 'Euro Stoxx 50 Volatility', value: 14.95, change: -0.42, changePct: -2.73, high: 15.63, low: 14.78, trend: generateTrend(16, 30, 0.9, -0.03) },
  { id: 'nkvi', name: 'NKVI', desc: 'Nikkei 225 Volatility', value: 18.34, change: 0.78, changePct: 4.44, high: 19.12, low: 17.89, trend: generateTrend(17, 30, 1.1, 0.04) },
  { id: 'rvx', name: 'RVX', desc: 'Russell 2000 Volatility', value: 20.14, change: -1.23, changePct: -5.76, high: 21.89, low: 19.87, trend: generateTrend(22, 30, 1.4, -0.06) },
  { id: 'move', name: 'MOVE', desc: 'US Bond Market Volatility', value: 108.34, change: 2.34, changePct: 2.21, high: 112.45, low: 106.78, trend: generateTrend(105, 30, 4, 0.02) },
];

export const macroVariables = [
  { id: 'uscpi', name: 'US CPI', desc: 'US Consumer Price Index', value: 3.2, unit: '%', prev: 3.5, forecast: 3.1, period: 'Jun 2026', type: 'inflation', trend: generateTrend(4.5, 24, 0.3, -0.03) },
  { id: 'uscorecpi', name: 'US Core CPI', desc: 'US Core CPI', value: 3.8, unit: '%', prev: 3.9, forecast: 3.7, period: 'Jun 2026', type: 'inflation', trend: generateTrend(5.2, 24, 0.25, -0.04) },
  { id: 'usppi', name: 'US PPI', desc: 'US Producer Price Index', value: 1.6, unit: '%', prev: 1.8, forecast: 1.5, period: 'Jun 2026', type: 'inflation', trend: generateTrend(3.2, 24, 0.4, -0.05) },
  { id: 'jpcpi', name: 'JP CPI', desc: 'Japan CPI', value: 2.8, unit: '%', prev: 2.6, forecast: 2.9, period: 'Jun 2026', type: 'inflation', trend: generateTrend(1.5, 24, 0.2, 0.04) },
  { id: 'eucpi', name: 'EU CPI', desc: 'EU CPI', value: 2.4, unit: '%', prev: 2.6, forecast: 2.3, period: 'Jun 2026', type: 'inflation', trend: generateTrend(6.8, 24, 0.45, -0.07) },
  { id: 'krcpi', name: 'KR CPI', desc: 'Korea CPI', value: 2.7, unit: '%', prev: 2.9, forecast: 2.6, period: 'Jun 2026', type: 'inflation', trend: generateTrend(3.6, 24, 0.2, -0.03) },
  { id: 'uspmi', name: 'US ISM PMI', desc: 'US ISM Manufacturing PMI', value: 48.7, unit: '', prev: 47.2, forecast: 48.5, period: 'Jun 2026', type: 'pmi', trend: generateTrend(50, 24, 1.2, -0.02) },
  { id: 'cnpmi', name: 'CN PMI', desc: 'China Manufacturing PMI', value: 50.3, unit: '', prev: 49.8, forecast: 50.0, period: 'Jun 2026', type: 'pmi', trend: generateTrend(49, 24, 0.8, 0.01) },
];

export const commodities = [
  { id: 'wti', name: 'WTI Crude', category: 'Energy', unit: 'USD/bbl', value: 78.23, change: 0.87, changePct: 1.12, high: 79.45, low: 77.12, trend: generateTrend(75, 30, 2.5, 0.05) },
  { id: 'brent', name: 'Brent Crude', category: 'Energy', unit: 'USD/bbl', value: 82.15, change: 0.92, changePct: 1.13, high: 83.34, low: 81.12, trend: generateTrend(79, 30, 2.6, 0.05) },
  { id: 'natgas', name: 'Natural Gas', category: 'Energy', unit: 'USD/MMBtu', value: 2.34, change: -0.08, changePct: -3.31, high: 2.48, low: 2.28, trend: generateTrend(2.8, 30, 0.12, -0.03) },
  { id: 'gold', name: 'Gold', category: 'Precious Metals', unit: 'USD/troy oz', value: 2341.50, change: 12.30, changePct: 0.53, high: 2358.40, low: 2328.60, trend: generateTrend(2100, 30, 25, 0.08) },
  { id: 'silver', name: 'Silver', category: 'Precious Metals', unit: 'USD/troy oz', value: 27.43, change: 0.34, changePct: 1.25, high: 27.89, low: 27.12, trend: generateTrend(25, 30, 0.5, 0.06) },
  { id: 'copper', name: 'Copper', category: 'Base Metals', unit: 'USD/lb', value: 4.52, change: -0.07, changePct: -1.53, high: 4.63, low: 4.48, trend: generateTrend(4.2, 30, 0.12, 0.04) },
  { id: 'alum', name: 'Aluminium', category: 'Base Metals', unit: 'USD/MT', value: 2345.00, change: 23.50, changePct: 1.01, high: 2378.00, low: 2312.00, trend: generateTrend(2200, 30, 30, 0.04) },
  { id: 'iron', name: 'Iron Ore', category: 'Industrial', unit: 'USD/MT', value: 108.45, change: -2.15, changePct: -1.94, high: 112.30, low: 107.23, trend: generateTrend(120, 30, 4, -0.05) },
];

export const yieldCurveUS = [
  { tenor: '1M', yield: 5.34, prev: 5.32 },
  { tenor: '3M', yield: 5.38, prev: 5.37 },
  { tenor: '6M', yield: 5.32, prev: 5.34 },
  { tenor: '1Y', yield: 5.12, prev: 5.18 },
  { tenor: '2Y', yield: 4.82, prev: 4.87 },
  { tenor: '3Y', yield: 4.61, prev: 4.68 },
  { tenor: '5Y', yield: 4.38, prev: 4.44 },
  { tenor: '7Y', yield: 4.33, prev: 4.40 },
  { tenor: '10Y', yield: 4.25, prev: 4.31 },
  { tenor: '20Y', yield: 4.48, prev: 4.53 },
  { tenor: '30Y', yield: 4.40, prev: 4.45 },
];

export const yieldCurveKR = [
  { tenor: '1Y', yield: 3.45, prev: 3.47 },
  { tenor: '2Y', yield: 3.52, prev: 3.54 },
  { tenor: '3Y', yield: 3.48, prev: 3.51 },
  { tenor: '5Y', yield: 3.56, prev: 3.59 },
  { tenor: '7Y', yield: 3.64, prev: 3.67 },
  { tenor: '10Y', yield: 3.72, prev: 3.75 },
  { tenor: '20Y', yield: 3.82, prev: 3.85 },
  { tenor: '30Y', yield: 3.75, prev: 3.79 },
];

export const krSwapRates = [
  { tenor: '1Y', irs: 3.42, crs: 3.15, irsChange: -0.03, crsChange: -0.05 },
  { tenor: '2Y', irs: 3.38, crs: 3.08, irsChange: -0.02, crsChange: -0.04 },
  { tenor: '3Y', irs: 3.35, crs: 3.05, irsChange: -0.02, crsChange: -0.03 },
  { tenor: '5Y', irs: 3.44, crs: 3.12, irsChange: -0.01, crsChange: -0.04 },
  { tenor: '7Y', irs: 3.58, crs: 3.22, irsChange: 0.01, crsChange: -0.02 },
  { tenor: '10Y', irs: 3.67, crs: 3.25, irsChange: 0.02, crsChange: -0.03 },
];

export const moneyMarket = [
  { name: 'Fed Funds Rate', value: 5.25, change: 0.00, period: 'Current', flag: '🇺🇸' },
  { name: 'SOFR', value: 5.31, change: 0.01, period: '7/17/2026', flag: '🇺🇸' },
  { name: 'US 3M T-Bill', value: 5.38, change: 0.01, period: 'Jul 2026', flag: '🇺🇸' },
  { name: 'EURIBOR 3M', value: 3.21, change: -0.02, period: 'Jul 2026', flag: '🇪🇺' },
  { name: 'LIBOR JPY 3M', value: 0.08, change: 0.01, period: 'Jul 2026', flag: '🇯🇵' },
  { name: 'KORIBOR 3M', value: 3.72, change: -0.01, period: 'Jul 2026', flag: '🇰🇷' },
  { name: 'CD 91-Day', value: 3.65, change: 0.00, period: '7/17/2026', flag: '🇰🇷' },
  { name: 'BOK Rate', value: 3.25, change: 0.00, period: 'Current', flag: '🇰🇷' },
];

export const freightIndices = [
  { id: 'bdi', name: 'BDI', fullName: 'Baltic Dry Index', value: 1842, change: 23, changePct: 1.27, desc: 'Dry Bulk Freight', trend: generateTrend(1600, 90, 60, 0.03) },
  { id: 'scfi', name: 'SCFI', fullName: 'Shanghai Containerized Freight Index', value: 2456, change: -45, changePct: -1.80, desc: 'Shanghai Container Freight', trend: generateTrend(1800, 90, 100, 0.04) },
  { id: 'ccfi', name: 'CCFI', fullName: 'China Containerized Freight Index', value: 1923, change: 12, changePct: 0.63, desc: 'China Container Freight', trend: generateTrend(1600, 90, 80, 0.03) },
  { id: 'wci', name: 'WCI', fullName: 'World Container Index (Drewry)', value: 3456, change: -123, changePct: -3.44, desc: 'Global Container Freight ($/FEU)', trend: generateTrend(2800, 90, 120, 0.04) },
  { id: 'fbx', name: 'FBX', fullName: 'Freightos Baltic Index', value: 2789, change: 67, changePct: 2.46, desc: 'Global Container Freight ($/FEU)', trend: generateTrend(2300, 90, 100, 0.04) },
  { id: 'harpex', name: 'HARPEX', fullName: 'Harper Petersen Charter Rates Index', value: 843, change: -12, changePct: -1.40, desc: 'Container Charter Rate', trend: generateTrend(900, 90, 40, -0.02) },
];

export const portMarkers = [
  { id: 'sha', name: 'Shanghai', city: 'Shanghai', country: 'China', coords: [121.4737, 31.2304] as [number, number], index: 'SCFI', value: 2456, change: -1.80, unit: 'pts', prev: 2501, date: '2026-07-15' },
  { id: 'rot', name: 'Rotterdam', city: 'Rotterdam', country: 'Netherlands', coords: [4.4777, 51.9244] as [number, number], index: 'BFAI-EU', value: 1823, change: 0.92, unit: 'pts', prev: 1806, date: '2026-07-15' },
  { id: 'lax', name: 'Los Angeles', city: 'Los Angeles', country: 'USA', coords: [-118.2437, 34.0522] as [number, number], index: 'TPEB', value: 3210, change: -2.15, unit: '$/FEU', prev: 3281, date: '2026-07-15' },
  { id: 'sin', name: 'Singapore', city: 'Singapore', country: 'Singapore', coords: [103.8198, 1.3521] as [number, number], index: 'SFIA', value: 1654, change: 1.23, unit: 'pts', prev: 1634, date: '2026-07-15' },
  { id: 'ham', name: 'Hamburg', city: 'Hamburg', country: 'Germany', coords: [9.9937, 53.5753] as [number, number], index: 'BSI-C5', value: 1245, change: -0.64, unit: 'pts', prev: 1253, date: '2026-07-15' },
  { id: 'bus', name: 'Busan', city: 'Busan', country: 'South Korea', coords: [129.0756, 35.1796] as [number, number], index: 'KEFFA', value: 1134, change: 0.45, unit: 'pts', prev: 1129, date: '2026-07-15' },
  { id: 'dub', name: 'Dubai', city: 'Dubai', country: 'UAE', coords: [55.2708, 25.2048] as [number, number], index: 'MENA FI', value: 987, change: 1.85, unit: 'pts', prev: 969, date: '2026-07-15' },
  { id: 'nyk', name: 'New York', city: 'New York', country: 'USA', coords: [-74.0059, 40.7128] as [number, number], index: 'TATB', value: 2890, change: -1.02, unit: '$/FEU', prev: 2920, date: '2026-07-15' },
];

export const countryMacroData: Record<string, { iso: string; name: string; flag: string; cpi: number; cpiChange: number; gdp: number; gdpChange: number; unemploy: number; pmi: number; rate: number; date: string }> = {
  US: { iso: 'US', name: 'USA', flag: '🇺🇸', cpi: 3.2, cpiChange: -0.3, gdp: 2.9, gdpChange: 0.2, unemploy: 3.7, pmi: 48.7, rate: 5.25, date: 'Jun 2026' },
  JP: { iso: 'JP', name: 'Japan', flag: '🇯🇵', cpi: 2.8, cpiChange: 0.2, gdp: 0.4, gdpChange: -0.1, unemploy: 2.4, pmi: 50.2, rate: 0.10, date: 'Jun 2026' },
  DE: { iso: 'DE', name: 'Germany', flag: '🇩🇪', cpi: 2.4, cpiChange: -0.2, gdp: -0.3, gdpChange: -0.5, unemploy: 5.9, pmi: 43.4, rate: 4.25, date: 'Jun 2026' },
  GB: { iso: 'GB', name: 'UK', flag: '🇬🇧', cpi: 3.4, cpiChange: -0.1, gdp: 0.3, gdpChange: 0.1, unemploy: 4.2, pmi: 50.9, rate: 5.00, date: 'Jun 2026' },
  FR: { iso: 'FR', name: 'France', flag: '🇫🇷', cpi: 2.4, cpiChange: -0.3, gdp: 0.2, gdpChange: 0.0, unemploy: 7.3, pmi: 45.3, rate: 4.25, date: 'Jun 2026' },
  CN: { iso: 'CN', name: 'China', flag: '🇨🇳', cpi: 0.1, cpiChange: 0.0, gdp: 5.0, gdpChange: -0.2, unemploy: 5.0, pmi: 50.3, rate: 3.45, date: 'Jun 2026' },
  KR: { iso: 'KR', name: 'Korea', flag: '🇰🇷', cpi: 2.7, cpiChange: -0.2, gdp: 2.4, gdpChange: 0.3, unemploy: 2.8, pmi: 49.8, rate: 3.25, date: 'Jun 2026' },
  IN: { iso: 'IN', name: 'India', flag: '🇮🇳', cpi: 4.9, cpiChange: -0.3, gdp: 7.8, gdpChange: 0.1, unemploy: 7.5, pmi: 57.5, rate: 6.50, date: 'Jun 2026' },
  BR: { iso: 'BR', name: 'Brazil', flag: '🇧🇷', cpi: 3.8, cpiChange: -0.4, gdp: 2.1, gdpChange: -0.2, unemploy: 7.8, pmi: 52.1, rate: 10.50, date: 'Jun 2026' },
  AU: { iso: 'AU', name: 'Australia', flag: '🇦🇺', cpi: 3.6, cpiChange: -0.2, gdp: 1.4, gdpChange: 0.1, unemploy: 4.1, pmi: 51.2, rate: 4.35, date: 'Jun 2026' },
};

export const macroCalendar = [
  { country: '🇺🇸', event: 'Non-Farm Payrolls', actual: 206, forecast: 185, prev: 272, period: 'Jun 2026', importance: 'high' },
  { country: '🇺🇸', event: 'CPI YoY', actual: 3.2, forecast: 3.1, prev: 3.5, period: 'Jun 2026', importance: 'high' },
  { country: '🇺🇸', event: 'Core CPI MoM', actual: 0.3, forecast: 0.3, prev: 0.4, period: 'Jun 2026', importance: 'high' },
  { country: '🇺🇸', event: 'Retail Sales MoM', actual: 0.6, forecast: 0.3, prev: -0.2, period: 'Jun 2026', importance: 'medium' },
  { country: '🇺🇸', event: 'GDP QoQ (Annl)', actual: 2.9, forecast: 2.8, prev: 3.4, period: 'Q1 2026', importance: 'high' },
  { country: '🇯🇵', event: 'CPI YoY', actual: 2.8, forecast: 2.9, prev: 2.6, period: 'Jun 2026', importance: 'high' },
  { country: '🇯🇵', event: 'Trade Balance', actual: 0.2, forecast: 0.4, prev: -0.1, period: 'Jun 2026', importance: 'medium' },
  { country: '🇪🇺', event: 'CPI YoY', actual: 2.4, forecast: 2.3, prev: 2.6, period: 'Jun 2026', importance: 'high' },
  { country: '🇪🇺', event: 'GDP QoQ', actual: 0.4, forecast: 0.3, prev: 0.3, period: 'Q1 2026', importance: 'high' },
  { country: '🇨🇳', event: 'Caixin PMI Mfg', actual: 50.4, forecast: 50.2, prev: 50.0, period: 'Jun 2026', importance: 'high' },
  { country: '🇨🇳', event: 'Trade Balance', actual: 72.4, forecast: 65.0, prev: 68.5, period: 'Jun 2026', importance: 'medium' },
  { country: '🇰🇷', event: 'CPI YoY', actual: 2.7, forecast: 2.6, prev: 2.9, period: 'Jun 2026', importance: 'high' },
  { country: '🇰🇷', event: 'GDP QoQ', actual: 0.6, forecast: 0.5, prev: 0.3, period: 'Q1 2026', importance: 'high' },
  { country: '🇬🇧', event: 'CPI YoY', actual: 3.4, forecast: 3.3, prev: 3.5, period: 'Jun 2026', importance: 'high' },
  { country: '🇮🇳', event: 'CPI YoY', actual: 4.9, forecast: 5.0, prev: 5.2, period: 'Jun 2026', importance: 'medium' },
];

export const countryMarkers = [
  { country: 'US', coords: [-100.0, 40.0] as [number, number] },
  { country: 'JP', coords: [138.0, 36.0] as [number, number] },
  { country: 'DE', coords: [10.0, 51.5] as [number, number] },
  { country: 'GB', coords: [-2.0, 54.0] as [number, number] },
  { country: 'FR', coords: [2.3, 46.2] as [number, number] },
  { country: 'CN', coords: [104.0, 35.0] as [number, number] },
  { country: 'KR', coords: [127.5, 36.5] as [number, number] },
  { country: 'IN', coords: [78.9, 20.6] as [number, number] },
  { country: 'BR', coords: [-51.9, -14.2] as [number, number] },
  { country: 'AU', coords: [133.7, -25.3] as [number, number] },
];

export const industryData = [
  { id: 'dram', name: 'DRAM Spot (DDR5)', category: 'Semiconductors', unit: 'USD/unit', value: 28.50, change: 0.75, changePct: 2.71, high: 29.10, low: 27.80, trend: generateTrend(24, 30, 1.2, 0.1) },
  { id: 'nand', name: 'NAND Flash 128Gb', category: 'Semiconductors', unit: 'USD/unit', value: 4.85, change: -0.12, changePct: -2.41, high: 5.10, low: 4.78, trend: generateTrend(4.2, 30, 0.2, 0.04) },
  { id: 'hbm3', name: 'HBM3 Memory', category: 'Semiconductors', unit: 'USD/unit', value: 14.20, change: 0.45, changePct: 3.27, high: 14.65, low: 13.90, trend: generateTrend(11, 30, 0.6, 0.12) },
  { id: 'siwaf', name: 'Silicon Wafer 300mm', category: 'Semiconductors', unit: 'USD/unit', value: 8.45, change: 0.05, changePct: 0.60, high: 8.60, low: 8.38, trend: generateTrend(8.0, 30, 0.15, 0.02) },
  { id: 'gasus', name: 'US Gasoline', category: 'Energy & Fuel', unit: 'USD/gal', value: 2.45, change: -0.03, changePct: -1.21, high: 2.52, low: 2.41, trend: generateTrend(2.7, 30, 0.1, -0.03) },
  { id: 'diesel', name: 'Diesel (ULSD)', category: 'Energy & Fuel', unit: 'USD/gal', value: 2.78, change: -0.05, changePct: -1.77, high: 2.87, low: 2.74, trend: generateTrend(3.1, 30, 0.12, -0.04) },
  { id: 'cshome', name: 'CS Home Price Idx', category: 'Real Estate', unit: 'Index', value: 323.4, change: 1.2, changePct: 0.37, high: 324.1, low: 321.8, trend: generateTrend(295, 30, 4, 0.06) },
  { id: 'krapti', name: 'KR Apt Price Idx', category: 'Real Estate', unit: 'Index', value: 113.2, change: 0.3, changePct: 0.27, high: 113.5, low: 112.8, trend: generateTrend(108, 30, 1.2, 0.04) },
  { id: 'poly', name: 'Polysilicon', category: 'Materials', unit: 'USD/kg', value: 6.23, change: -0.18, changePct: -2.81, high: 6.54, low: 6.12, trend: generateTrend(9, 30, 0.4, -0.08) },
  { id: 'lithi', name: 'Lithium Carbonate', category: 'Materials', unit: 'USD/MT', value: 12450, change: -230, changePct: -1.81, high: 12890, low: 12340, trend: generateTrend(18000, 30, 500, -0.1) },
  { id: 'cobalt', name: 'Cobalt', category: 'Materials', unit: 'USD/MT', value: 24890, change: 320, changePct: 1.30, high: 25200, low: 24560, trend: generateTrend(22000, 30, 600, 0.05) },
  { id: 'steel', name: 'HRC Steel', category: 'Steel & Metals', unit: 'USD/MT', value: 785, change: -8, changePct: -1.01, high: 798, low: 779, trend: generateTrend(850, 30, 20, -0.04) },
];

export const sentimentData = {
  fng: { value: 62, label: 'Greed', connected: true, color: '#16A34A', trend: generateTrend(45, 30, 8, 0.03) },
  aaii: { value: 45.2, prev: 44.1, bullish: 45.2, bearish: 28.6, neutral: 26.2, connected: true, trend: generateTrend(38, 30, 4, 0.02) },
  naaim: { value: 68.3, change: 3.2, connected: true, trend: generateTrend(60, 30, 5, 0.02) },
  putcall: { value: 0.82 as number | null, change: -0.05, connected: true, reason: '', trend: generateTrend(1.0, 30, 0.08, -0.02) },
};

const tickerDefinitions = [
  ['spx','SPX','Equity'], ['nasdaq','NASDAQ','Equity'], ['russell2000','RUSSELL 2000','Equity'], ['soxx','SOXX','Equity'],
  ['kospi','KOSPI','Equity'], ['kosdaq','KOSDAQ','Equity'], ['nikkei225','NIKKEI 225','Equity'], ['topix','TOPIX','Equity'],
  ['csi300','CSI 300','Equity'], ['shenzhen','SHENZHEN','Equity'], ['hsi','HSI','Equity'], ['eurostoxx50','EURO STOXX 50','Equity'],
  ['vix','VIX','Volatility'], ['vvix','VVIX','Volatility'], ['skew','SKEW','Volatility'], ['vkospi','VKOSPI','Volatility'], ['nkvi','NKVI','Volatility'],
  ['us3m','US 3M','Rates'], ['us2y','US 2Y','Rates'], ['us10y','US 10Y','Rates'], ['kr3y','KR 3Y','Rates'], ['kr10y','KR 10Y','Rates'],
  ['wti','WTI','Commodity'], ['gold','GOLD','Commodity'], ['silver','SILVER','Commodity'],
  ['dxi','DXI','Industry'],
  ['bdi','BDI','Freight'], ['bci','BCI','Freight'], ['bdti','BDTI','Freight'], ['bhsi','BHSI','Freight'], ['blng','BLNG','Freight'], ['blpg','BLPG','Freight'],
  ['ccfi','CCFI','Freight'], ['scfi','SCFI','Freight'], ['wci','WCI','Freight'],
  ['bitcoin','BITCOIN','Crypto'], ['ethereum','ETHEREUM','Crypto'],
  ['dxy','DOLLAR INDEX','FX'], ['jxy','YEN INDEX','FX'], ['exy','EURO INDEX','FX'],
] as const;

export const tickerTape = tickerDefinitions.map(([id, name, category]) => ({
  id, name, category, value: null as number | null, change: null as number | null,
  changePct: null as number | null, connected: false, asOf: null as string | null,
}));

export const newsFeed = [
  { id: 1, time: '13:42', source: 'Reuters', title: 'Fed official signals cautious approach to rate cuts this year', tag: 'Monetary Policy', sentiment: 'neutral' },
  { id: 2, time: '13:28', source: 'Bloomberg', title: 'S&P 500 approaches all-time high as AI-related stocks lead rally', tag: 'US Stocks', sentiment: 'positive' },
  { id: 3, time: '13:15', source: 'Yonhap', title: 'Samsung Electronics expands HBM3 supply deal; Nvidia-bound volumes increase', tag: 'Semiconductors', sentiment: 'positive' },
  { id: 4, time: '13:02', source: 'FT', title: 'ECB president says disinflation ongoing in Europe, room for further cuts', tag: 'Europe', sentiment: 'positive' },
  { id: 5, time: '12:48', source: 'Hankyung', title: 'KOSPI expected to close slightly lower on foreign net selling', tag: 'Korea Stocks', sentiment: 'negative' },
  { id: 6, time: '12:33', source: 'Nikkei', title: 'BOJ weighing additional short-term rate hike; yen strengthens', tag: 'Japan', sentiment: 'neutral' },
  { id: 7, time: '12:19', source: 'CNBC', title: 'Crude inventories beat expectations; WTI holds $78 level', tag: 'Commodities', sentiment: 'neutral' },
  { id: 8, time: '12:05', source: 'Edaily', title: 'Korea 10Y gov bond at 3.72%; foreigners buying bond futures', tag: 'Bonds', sentiment: 'positive' },
];

export const sectorData = [
  { name: 'Technology', ko: 'Technology', changePct: 1.24, value: 3456.78, marketCap: '12.4T' },
  { name: 'Communication', ko: 'Communication', changePct: 1.51, value: 234.56, marketCap: '4.8T' },
  { name: 'Consumer Disc.', ko: 'Consumer Disc.', changePct: 0.89, value: 1876.43, marketCap: '7.2T' },
  { name: 'Financials', ko: 'Financials', changePct: 0.72, value: 634.21, marketCap: '9.8T' },
  { name: 'Industrials', ko: 'Industrials', changePct: 0.38, value: 897.34, marketCap: '5.6T' },
  { name: 'Real Estate', ko: 'Real Estate', changePct: 0.21, value: 234.12, marketCap: '1.2T' },
  { name: 'Consumer Staples', ko: 'Consumer Staples', changePct: 0.11, value: 765.43, marketCap: '3.9T' },
  { name: 'Materials', ko: 'Materials', changePct: -0.18, value: 534.67, marketCap: '2.8T' },
  { name: 'Health Care', ko: 'Health Care', changePct: -0.31, value: 1234.56, marketCap: '8.7T' },
  { name: 'Energy', ko: 'Energy', changePct: -0.52, value: 678.90, marketCap: '4.2T' },
  { name: 'Utilities', ko: 'Utilities', changePct: -0.78, value: 345.67, marketCap: '1.7T' },
];

export const krSectorData = [
  { name: 'Semiconductors', changePct: 1.82, value: 4823.45 },
  { name: 'IT Services', changePct: 0.95, value: 1234.56 },
  { name: 'Automotive', changePct: 0.32, value: 2345.67 },
  { name: 'Financials', changePct: 0.51, value: 876.54 },
  { name: 'Steel & Materials', changePct: 0.18, value: 543.21 },
  { name: 'Biotech', changePct: -0.72, value: 1456.78 },
  { name: 'Battery', changePct: -1.23, value: 987.65 },
  { name: 'Chemicals', changePct: -0.41, value: 654.32 },
];

export const sectorDataByCountry: Record<string, any[]> = {
  US: sectorData.map((item, index) => ({ ...item, id: `sector-us-${index}`, country: 'US' })),
  KR: krSectorData.map((item, index) => ({ ...item, id: `sector-kr-${index}`, country: 'KR' })),
  JP: [],
  CN: [],
};

// MSCI + Global Benchmark Indices (2x2 section on Overview)
export const globalBenchmarks = [
  {
    id: 'acwi', name: 'MSCI ACWI', desc: 'Global Equities (46 countries)', flag: '🌍',
    value: 823.45, change: 8.34, changePct: 1.02,
    ytd: 12.4, high52w: 841.23, low52w: 698.12,
    trend: generateTrend(720, 60, 12, 0.05),
  },
  {
    id: 'em', name: 'MSCI EM', desc: 'EM Equities (24 countries)', flag: '🌏',
    value: 1045.23, change: 8.89, changePct: 0.85,
    ytd: 8.7, high52w: 1092.34, low52w: 890.45,
    trend: generateTrend(950, 60, 18, 0.04),
  },
  {
    id: 'bond', name: 'MSCI Bond (BNDW)', desc: 'Global Bond Index', flag: '📊',
    value: 72.34, change: -0.09, changePct: -0.12,
    ytd: 2.1, high52w: 74.82, low52w: 69.14,
    trend: generateTrend(70, 60, 0.6, 0.01),
  },
  {
    id: 'djci', name: 'DJ Commodity', desc: 'DJ Commodity Index', flag: '⚡',
    value: 965.43, change: 6.45, changePct: 0.67,
    ytd: 5.3, high52w: 1012.56, low52w: 878.23,
    trend: generateTrend(890, 60, 14, 0.03),
  },
];

// Asset Allocation — Portfolio Optimization
export const portfolioAssets = [
  { id: 'us_eq', name: 'US Equities', ticker: 'SPX', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'United States', color: '#1A56DB' },
  { id: 'kr_eq', name: 'Korea Equities', ticker: 'KOSPI', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'South Korea', color: '#3B82F6' },
  { id: 'jp_eq', name: 'Japan Equities', ticker: 'N225', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'Japan', color: '#60A5FA' },
  { id: 'cn_eq', name: 'China Equities', ticker: 'CSI300', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'China', color: '#F59E0B' },
  { id: 'us_small', name: 'US Small Cap', ticker: 'RUS2000', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'United States', color: '#06B6D4' },
  { id: 'semi', name: 'Semiconductors', ticker: 'SOX', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'United States', color: '#8B5CF6' },
  { id: 'reit', name: 'US Real Estate', ticker: 'SPX RE', assetClass: 'Market', expectedReturn: 0, volatility: 0, region: 'United States', color: '#A855F7' },
  { id: 'kr_bond_3y', name: 'Korea Treasury 3Y', ticker: 'KTB 3Y', assetClass: 'Bond', expectedReturn: 0, volatility: 0, region: 'South Korea', color: '#22C55E' },
  { id: 'kr_bond_10y', name: 'Korea Treasury 10Y', ticker: 'KTB 10Y', assetClass: 'Bond', expectedReturn: 0, volatility: 0, region: 'South Korea', color: '#15803D' },
  { id: 'dxy', name: 'US Dollar Index', ticker: 'DXY', assetClass: 'FX', expectedReturn: 0, volatility: 0, region: 'FX', color: '#16A34A' },
  { id: 'jxy', name: 'Japanese Yen Index', ticker: 'JXY', assetClass: 'FX', expectedReturn: 0, volatility: 0, region: 'FX', color: '#E11D48' },
  { id: 'exy', name: 'Euro Currency Index', ticker: 'EXY', assetClass: 'FX', expectedReturn: 0, volatility: 0, region: 'FX', color: '#0EA5E9' },
];

export type PortfolioMethod = 'mvo' | 'hrp' | 'nco' | 'bl';

export interface MVOParams  { objective: 'mean_variance'|'min_variance'|'max_sharpe'; riskAversion: number; minWeight: number; maxWeight: number; longOnly: boolean }
export interface HRPParams  { linkage: string; distanceMetric: string }
export interface NCOParams  { nClusters: number; withinCluster: string; covEstimator: string }
export interface BLParams   { delta: number; tau: number; views: { assetId: string; direction: 'up'|'down'; magnitude: number; confidence: number }[] }

export type DashboardConnection = {
  connected: boolean;
  updatedAt?: string;
  source?: string;
  error?: string;
};

export const dashboardConnection: DashboardConnection = { connected: false };

function mergeArray(target: any[], incoming: any[] | undefined) {
  if (!incoming?.length) return;
  const byId = new Map(incoming.map(item => [item.id ?? item.tenor, item]));
  target.forEach((item, index) => {
    const live = byId.get(item.id ?? item.tenor);
    if (live) target[index] = { ...item, ...live };
  });
}

function replaceArray(target: any[], incoming: any[] | undefined) {
  if (!incoming?.length) return;
  target.splice(0, target.length, ...incoming);
}

export async function loadDashboardData(): Promise<DashboardConnection> {
  try {
    const response = await fetch('/api/dashboard');
    if (!response.ok) throw new Error(`API ${response.status}`);
    const data = await response.json();
    replaceArray(marketIndices, data.marketIndices);
    replaceArray(volatilityIndices, data.volatilityIndices);
    replaceArray(macroVariables, data.macroVariables);
    replaceArray(commodities, data.commodities);
    mergeArray(yieldCurveUS, data.yieldCurveUS);
    mergeArray(yieldCurveKR, data.yieldCurveKR);
    replaceArray(freightIndices, data.freightIndices);
    replaceArray(industryData, data.industryData);
    mergeArray(tickerTape, data.tickerTape);
    if (data.sectorDataByCountry) {
      Object.entries(data.sectorDataByCountry).forEach(([country, items]) => {
        if (Array.isArray(items) && items.length) sectorDataByCountry[country] = items;
      });
    }
    if (data.sentimentData) {
      Object.entries(data.sentimentData).forEach(([key, value]) => {
        if (value && typeof value === 'object' && key in sentimentData) {
          Object.assign((sentimentData as any)[key], value);
        }
      });
    }
    Object.assign(dashboardConnection, {
      connected: true,
      updatedAt: data.updatedAt,
      source: data.source,
      error: undefined,
    });
  } catch (error) {
    Object.assign(dashboardConnection, {
      connected: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }
  return dashboardConnection;
}
