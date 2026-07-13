(function () {
   var script = document.currentScript;
   if (!script) return;

   var baseUrl = script.src.replace(/[^/]*$/, '');

   var s = document.createElement('script');
   s.src = baseUrl + 'ramon-burble.js';
   s.defer = true;
   document.body.appendChild(s);
})();
