// Utilidad global para manejar URLs de imágenes (local vs Supabase)
window.resolveImageUrl = function(url, defaultPath = '/static/img/default-player.png') {
  if (!url) return defaultPath;
  
  const urlStr = String(url);
  
  // Si ya es una URL absoluta (http/https) o una ruta estática, usarla directamente
  if (urlStr.startsWith('http://') || urlStr.startsWith('https://') || urlStr.startsWith('/static/')) {
    return urlStr;
  }
  
  // Si es solo un nombre de archivo, construir ruta local
  return `/static/img/${urlStr}`;
};

window.setImageSrc = function(imgElement, url, defaultPath = '/static/img/default-player.png') {
  const resolvedUrl = window.resolveImageUrl(url, defaultPath);
  imgElement.src = resolvedUrl;
  
  // Agregar manejador de error para fallback
  imgElement.onerror = function() {
    if (this.src !== defaultPath) {
      this.src = defaultPath;
    }
  };
};
