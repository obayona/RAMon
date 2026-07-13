(function () {
   const config = window.__RAMON_CONFIG__;

   if (!config) {
      throw new Error(
         'RAMon config not found.',
      );
   }

   var assetsUrl = config.assetsUrl;

   var s = document.createElement('script');
   s.src = assetsUrlUrl + 'ramon-burble.js';
   s.defer = true;
   document.body.appendChild(s);
})();
