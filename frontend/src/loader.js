(function () {
   var script = document.currentScript;
   if (!script) return;

   var baseUrl = script.src.replace(/[^/]*$/, '');

   var link = document.createElement('link');
   link.rel = 'stylesheet';
   link.href = baseUrl + 'ramon-burble.css';
   document.head.appendChild(link);

   var s = document.createElement('script');
   s.src = baseUrl + 'ramon-burble.js';
   s.defer = true;
   document.body.appendChild(s);
})();
