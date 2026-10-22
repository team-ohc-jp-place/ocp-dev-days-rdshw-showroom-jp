// Preserve workshop user parameters and section bookmarks when old page URLs move.
module.exports.register = function () {
  this.on('redirectsProduced', ({ contentCatalog }) => {
    for (const file of contentCatalog.findBy({ family: 'alias' })) {
      if (!file.out || !file.contents) continue;
      let html = file.contents.toString();
      html = html.replace(/<script>location=("[^"]*")<\/script>/, (_, destination) =>
        `<script>const target=new URL(${destination},location.href);if(location.search)target.search=location.search;if(location.hash)target.hash=location.hash;location.replace(target.href)</script>`);
      html = html.replaceAll('Redirect Notice', 'ページの移動');
      html = html.replace(/The page you requested has been relocated to (.*)\.<\/p>/,
        'このページは $1 に移動しました。</p>');
      file.contents = Buffer.from(html);
    }
  });
};
