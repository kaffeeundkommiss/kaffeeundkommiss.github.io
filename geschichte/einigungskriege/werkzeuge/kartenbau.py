# Aufruf: python3 kartenbau.py <ordner-mit-geojson>/ ../karte-daten.js
# Benötigt shapely sowie world_1815.geojson (als w1815.json), ne_10m_admin_0_countries.json, ne_10m_admin_1_states_provinces.json
# Baut die Grundkarte (SVG-Pfade je Einheit) für die Übersicht Einigungskriege.
# Grundlage: aourednik/historical-basemaps world_1815 (GPL-3.0), Natural Earth 10m (gemeinfrei) für Benelux, Savoyen, Elsass-Lothringen.
import json, math, sys, warnings; warnings.filterwarnings("ignore")
from shapely.geometry import shape, box, Point
from shapely.ops import unary_union, transform
from shapely.validation import make_valid
G=sys.argv[1]; OUT=sys.argv[2]
LON0,LAT0,LON1,LAT1=-8,41,30,61
B=box(LON0,LAT0,LON1,LAT1)
p1,p2,l0,f0=math.radians(47),math.radians(54),math.radians(10),math.radians(51)
n=math.log(math.cos(p1)/math.cos(p2))/math.log(math.tan(math.pi/4+p2/2)/math.tan(math.pi/4+p1/2))
F=math.cos(p1)*math.tan(math.pi/4+p1/2)**n/n; r0=F/math.tan(math.pi/4+f0/2)**n
def P(lon,lat):
  r=F/math.tan(math.pi/4+math.radians(lat)/2)**n; t=n*(math.radians(lon)-l0)
  return r*math.sin(t), r0-r*math.cos(t)
def proj(x,y,z=None):
  o=[P(a,b) for a,b in zip(x,y)]; return [a for a,_ in o],[b for _,b in o]
h=json.load(open(G+'w1815.json'))
a0=json.load(open(G+'ne_10m_admin_0_countries.json'))
a1=json.load(open(G+'ne_10m_admin_1_states_provinces.json'))
def hb(*names, sub=None, filt=None):
  gs=[]
  for f in h['features']:
    p=f['properties']
    if p.get('NAME') in names or (sub and p.get('SUBJECTO')==sub and p.get('NAME') in names):
      g=make_valid(shape(f['geometry']))
      if filt and not filt(g): continue
      gs.append(g)
  return unary_union(gs)
def ne0(*codes): return unary_union([make_valid(shape(f['geometry'])) for f in a0['features'] if f['properties']['ADM0_A3'] in codes])
def ne1(*names): return unary_union([make_valid(shape(f['geometry'])) for f in a1['features'] if f['properties']['adm0_a3']=='FRA' and f['properties']['name'] in names])
benelux=ne0('NLD','BEL','LUX')
savoy=ne1('Savoie','Haute-Savoie')
alsace=ne1('Bas-Rhin','Haute-Rhin','Moselle')
U={}
U['DK']=hb('Denmark'); U['SCHL']=hb('Schleswig'); U['HOL']=hb('Holstein')
U['PR']=hb('Prussia','Hohenzollern','Wetzlar')
U['AT']=unary_union([hb('Austrian Empire'),hb('Republic of Kraków')]).difference(benelux.buffer(0.02))
U['VEN']=hb('Venetia')
sard=hb('Kingdom of Sardinia')
U['IT']=unary_union([sard.difference(savoy),hb('Lombardy','Parma','Modena','Tuscany','Lucca','Massa','Pontremoli','Fivizzano','Papal States')])
U['SAX']=hb('Saxony'); U['HAN']=hb('Hanover'); U['BAY']=hb('Bavaria','Palatinate'); U['WUE']=hb('Württemberg'); U['BAD']=hb('Baden')
U['OHES']=hb('Grand Duchy of Hesse',filt=lambda g:g.centroid.y>50.2)
U['HESD']=hb('Grand Duchy of Hesse',filt=lambda g:g.centroid.y<=50.2)
U['KUR']=hb('Electoral Hesse'); U['NAS']=hb('Nassau')
U['KLEIN']=hb('Mecklenburg-Strelitz','Mecklenburg-Schwerin','Waldeck','Lippe-Detmold','Brunswick','Anhalt','Thuringia','Lübeck','Oldenburg','Bremen','Cuxhaven','Hamburg','Schaumburg-Lippe')
fr=unary_union([hb('France').difference(benelux.buffer(0.02)),savoy.intersection(sard.buffer(0.05))])
U['ELS']=fr.intersection(alsace); U['FR']=fr.difference(alsace)
U['CH']=hb('Switzerland'); U['NL']=ne0('NLD'); U['BE']=ne0('BEL'); U['LU']=ne0('LUX')
U['GB']=hb('United Kingdom of Great Britain and Ireland'); U['SE']=hb('Sweden–Norway'); U['RU']=hb('Russian Empire'); U['OTT']=hb('Ottoman Empire')
U['SM']=hb('San Marino')
# Land insgesamt für Küstenhintergrund
land=unary_union([make_valid(shape(f['geometry'])) for f in h['features'] if shape(f['geometry']).intersects(B)])
U['REST']=land.difference(unary_union(list(U.values())).buffer(0.01))
minx=P(-0.8,47)[0]; maxx=P(22.5,50.5)[0]; miny=P(10,44.9)[1]; maxy=P(10,57.7)[1]
from shapely.geometry import box as _b
RECT=_b(minx,miny,maxx,maxy)
W=1000; s=W/(maxx-minx); H=(maxy-miny)*s
def xy(lon,lat):
  x,y=P(lon,lat); return round((x-minx)*s,1), round((maxy-y)*s,1)
def path(g):
  g=make_valid(transform(proj,g.intersection(B).simplify(0.008))).intersection(RECT); out=[]
  polys=[g] if g.geom_type=='Polygon' else [q for q in getattr(g,'geoms',[]) if q.geom_type=='Polygon']
  for p in polys:
    if p.area*s*s<1.5: continue
    for ring in [p.exterior,*p.interiors]:
      pts=[f'{(x-minx)*s:.1f},{(maxy-y)*s:.1f}' for x,y in ring.coords]
      out.append('M'+'L'.join(pts)+'Z')
  return ''.join(out)
res={'W':W,'H':round(H),'units':{k:path(v) for k,v in U.items()}}
# Projektionshilfe für Orte
orte={'Berlin':(13.40,52.52),'Wien':(16.37,48.21),'Kopenhagen':(12.57,55.68),'Paris':(2.35,48.86),'München':(11.58,48.14),'Dresden':(13.74,51.05),
 'Hannover':(9.73,52.37),'Frankfurt':(8.68,50.11),'Stuttgart':(9.18,48.78),'Karlsruhe':(8.40,49.01),'Kassel':(9.50,51.31),
 'Düppel':(9.73,54.91),'Königgrätz':(15.83,50.21),'Langensalza':(10.65,51.11),'Custozza':(10.80,45.38),'Sedan':(4.94,49.70),'Metz':(6.18,49.12),
 'Versailles':(2.13,48.80),'Gravelotte':(6.03,49.11),'Wörth':(7.71,48.94),'Spichern':(6.97,49.20),'Mars-la-Tour':(5.89,49.10),'Le Mans':(0.20,48.00),'Kiel':(10.13,54.32),'Gastein':(13.10,47.11),'Prag':(14.42,50.08),'Nikolsburg':(16.64,48.80),'Frankfurt (Friede)':(8.68,50.11),'Turin':(7.69,45.07),'Bern':(7.45,46.95),'Brüssel':(4.35,50.85),'Amsterdam':(4.90,52.37)}
res['orte']={k:xy(*v) for k,v in orte.items()}
# Beschriftungspunkte je Einheit
lab={}
for k,v in U.items():
  g=make_valid(transform(proj,v.intersection(B))).intersection(RECT)
  if g.is_empty: continue
  big=max([q for q in getattr(g,'geoms',[g]) if q.geom_type=='Polygon'],key=lambda q:q.area)
  c=big.representative_point(); lab[k]=(round((c.x-minx)*s,1),round((maxy-c.y)*s,1))
res['lab']=lab
open(OUT,'w').write('// Erzeugt mit werkzeuge/kartenbau.py, nicht von Hand ändern.\n// Grenzen: aourednik/historical-basemaps world_1815 (GPL-3.0) und Natural Earth 10m (gemeinfrei), Änderungen bis 1871 nachgebaut.\nwindow.KARTE='+json.dumps(res,ensure_ascii=False,separators=(',',':'))+';\n')
print(res['W'],res['H'],{k:len(v) for k,v in res['units'].items()}, sum(len(v) for v in res['units'].values()))
