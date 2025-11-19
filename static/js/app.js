// Handle capture button on both home and gallery pages
(async function(){
    function $(s){return document.querySelector(s)}
    const btn = $('#capture-btn');
    if(btn){
        btn.addEventListener('click', async ()=>{
            const msg = $('#capture-msg');
            btn.disabled = true; if(msg) msg.textContent = 'Capturing...';
            try{
                const res = await fetch('/capture',{method:'POST'});
                const j = await res.json();
                if(res.ok){
                    if(msg) msg.textContent = 'Done';
                    if(window.fetchImages) await window.fetchImages();
                    setTimeout(()=>{ if(msg) msg.textContent=''; btn.disabled=false; }, 700);
                }else{
                    if(msg) msg.textContent = 'Error: '+(j.error||res.statusText);
                    btn.disabled = false;
                }
            }catch(e){ if($('#capture-msg')) $('#capture-msg').textContent = 'Error: '+e; btn.disabled = false; }
        });
    }

    // fetch and append new images
    window.fetchImages = async function(){
        try{
            const res = await fetch('/images'); if(!res.ok) return;
            const data = await res.json();
            const gallery = document.getElementById('gallery'); if(!gallery) return;
            const existing = new Set(Array.from(gallery.querySelectorAll('img')).map(i=>i.getAttribute('data-fname')));
            data.images.forEach(fname=>{
                if(!existing.has(fname)){
                    const img = document.createElement('img');
                    img.src = '/img/'+fname; img.alt = fname; img.setAttribute('data-fname', fname);
                    gallery.insertAdjacentElement('afterbegin', img);
                }
            });
        }catch(e){console.log('fetchImages error', e)}
    }

    // simple infinite reveal: initially hide items beyond 12
    if(document.getElementById('gallery')){
        const all = Array.from(document.querySelectorAll('.gallery img'));
        all.forEach((el,idx)=>{ if(idx>=12) el.style.opacity=0; });
        let i = Math.min(12, all.length);
        window.addEventListener('scroll', ()=>{
            const imgs = document.querySelectorAll('.gallery img');
            if(window.innerHeight + window.scrollY >= document.body.offsetHeight - 800){
                for(let j=0;j<12 && i<imgs.length;j++,i++) imgs[i].style.opacity = 1;
            }
        });
    }
})();