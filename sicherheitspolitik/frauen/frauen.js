// Hinweise beim Zeigen oder Antippen der Messpunkte im Diagramm „Anteil der Soldatinnen“. Ohne JavaScript bleiben Diagramm und Tabelle lesbar.
(function(){
  var fig=document.getElementById('frauenanteil'); if(!fig) return;
  var svg=fig.querySelector('svg'), tip=fig.querySelector('.ag-tip');
  var hinweis={eine:'eine Quelle',abw:'abweichende Werte'};
  function zeige(c){
    var t='<b>'+c.dataset.j+'</b>: '+c.dataset.w+' %<br>Quelle '+c.dataset.q.replace(',',', ');
    if(hinweis[c.dataset.h]) t+=' ('+hinweis[c.dataset.h]+')';
    tip.innerHTML=t; tip.hidden=false;
    var b=svg.getBoundingClientRect(), f=b.width/svg.viewBox.baseVal.width;
    var px=+c.getAttribute('cx')*f, py=+c.getAttribute('cy')*f, w=tip.offsetWidth;
    var l=px+12; if(l+w>b.width) l=px-w-12;
    tip.style.left=Math.max(0,l)+'px'; tip.style.top=Math.max(0,py-10)+'px';
  }
  function weg(){tip.hidden=true;}
  svg.querySelectorAll('.fa-pkt').forEach(function(c){
    c.addEventListener('mouseenter',function(){zeige(c)});
    c.addEventListener('focus',function(){zeige(c)});
    c.addEventListener('blur',weg);
    c.addEventListener('touchstart',function(){zeige(c)},{passive:true});
  });
  svg.addEventListener('mouseleave',weg);
})();
