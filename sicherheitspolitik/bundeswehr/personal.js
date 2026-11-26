// Interaktion für das Diagramm „Truppenstärke seit 1955“: Werte je Jahr beim Überfahren
// oder Antippen, Sprung zu den Brüchen über die Ereignisliste, Vergleichsreihe ein- und ausblenden.
// Es gibt eine breite und eine schmale Fassung des Diagramms; sichtbar ist je nach Bildschirm eine.
// Ohne JavaScript bleiben Diagramm, Ereignisliste und Tabelle lesbar.
(function(){
  var fig=document.getElementById('personal-diagramm'); if(!fig) return;
  var tip=fig.querySelector('.pz-tip'), svgs=fig.querySelectorAll('.pz-svg');
  function sichtbar(){for(var i=0;i<svgs.length;i++){if(svgs[i].getBoundingClientRect().width>0) return svgs[i];} return svgs[0];}
  function weg(){tip.hidden=true;svgs.forEach(function(s){s.querySelector('.pz-kreuz').setAttribute('hidden','');});}
  function zeige(r){
    var svg=r.ownerSVGElement, kreuz=svg.querySelector('.pz-kreuz');
    var x=+r.getAttribute('x')+(+r.getAttribute('width'))/2, d=r.dataset;
    kreuz.setAttribute('x1',x);kreuz.setAttribute('x2',x);kreuz.removeAttribute('hidden');
    var t='<b>'+d.j+'</b>';
    if(d.e) t+='<br><i>'+d.e+'</i>';
    if(d.w) t+='<br>Jahresdurchschnitt: '+d.w;
    else if(+d.j<1959) t+='<br>kein Jahreswert';
    if(d.s) t+='<br>Stichtag 3.10.: '+d.s;
    if(d.m) t+='<br>Monatswert: '+d.m;
    if(d.c && !fig.classList.contains('pz-ohne-cow')) t+='<br>COW (1. Januar): '+d.c;
    tip.innerHTML=t;tip.hidden=false;
    var b=svg.getBoundingClientRect().width, f=b/svg.viewBox.baseVal.width, px=x*f, w=tip.offsetWidth;
    var links=px+10; if(links+w>b) links=px-w-10;
    tip.style.left=Math.max(0,Math.min(links,b-w))+'px';
  }
  svgs.forEach(function(svg){
    svg.querySelectorAll('.pz-hit').forEach(function(r){
      r.addEventListener('mouseenter',function(){zeige(r)});
      r.addEventListener('touchstart',function(){zeige(r)},{passive:true});
    });
    svg.addEventListener('mouseleave',weg);
  });
  fig.querySelectorAll('.pz-ereignis').forEach(function(k){
    k.addEventListener('click',function(){
      var r=sichtbar().querySelector('.pz-hit[data-j="'+k.dataset.j+'"]'); if(!r) return;
      fig.querySelectorAll('.pz-ereignis[aria-current]').forEach(function(a){a.removeAttribute('aria-current')});
      k.setAttribute('aria-current','true');
      zeige(r);
    });
  });
  var sch=fig.querySelector('.pz-schalter');
  if(sch) sch.addEventListener('click',function(){
    var an=sch.getAttribute('aria-pressed')==='true';
    sch.setAttribute('aria-pressed',an?'false':'true');
    sch.textContent=an?'Vergleichsreihe einblenden':'Vergleichsreihe ausblenden';
    fig.classList.toggle('pz-ohne-cow',an);
    weg();
  });
})();
