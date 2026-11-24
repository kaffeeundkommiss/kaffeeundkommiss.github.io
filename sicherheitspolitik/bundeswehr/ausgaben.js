// Hover-Anzeige für das Ausgaben-Diagramm (Block 6). Ohne JavaScript bleiben Diagramm und Tabelle lesbar.
(function(){
  var fig=document.getElementById('ausgaben-diagramm'); if(!fig) return;
  var svg=fig.querySelector('svg'), tip=fig.querySelector('.ag-tip'), kreuz=fig.querySelector('.ag-kreuz');
  function zeige(r){
    var x=+r.getAttribute('x')+(+r.getAttribute('width'))/2;
    kreuz.setAttribute('x1',x);kreuz.setAttribute('x2',x);kreuz.removeAttribute('hidden');
    var t='<b>'+r.dataset.j+'</b><br>SIPRI: '+r.dataset.s+' %';
    if(r.dataset.n) t+='<br>NATO: '+r.dataset.n+' %';
    tip.innerHTML=t;tip.hidden=false;
    var f=svg.getBoundingClientRect().width/svg.viewBox.baseVal.width, px=x*f, w=tip.offsetWidth;
    tip.style.left=Math.max(0,Math.min(px+10,svg.getBoundingClientRect().width-w))+'px';
    if(px+10+w>svg.getBoundingClientRect().width) tip.style.left=Math.max(0,px-w-10)+'px';
  }
  function weg(){tip.hidden=true;kreuz.setAttribute('hidden','');}
  svg.querySelectorAll('.ag-hit').forEach(function(r){
    r.addEventListener('mouseenter',function(){zeige(r)});
    r.addEventListener('touchstart',function(){zeige(r)},{passive:true});
  });
  svg.addEventListener('mouseleave',weg);
})();
