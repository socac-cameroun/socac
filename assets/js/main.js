(function(){
  const toggle=document.querySelector('.mobile-toggle');
  const nav=document.querySelector('header nav');
  if(toggle && nav){
    toggle.addEventListener('click', function(){
      const open=nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent=open ? '✕' : '☰';
    });
  }
  const links=document.querySelectorAll('nav a[href^="#"]');
  const sections=[...document.querySelectorAll('main section[id]')];
  function activate(){
    const y=window.scrollY+120;
    let current='';
    sections.forEach(sec=>{ if(sec.offsetTop<=y) current=sec.id; });
    links.forEach(a=>a.classList.toggle('active', a.getAttribute('href')==='#'+current));
  }
  window.addEventListener('scroll', activate);
  activate();
  document.querySelectorAll('[data-year]').forEach(el=>el.textContent=new Date().getFullYear());
})();