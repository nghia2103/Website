document.addEventListener('DOMContentLoaded', function() {
  const select = document.querySelector('.country-codeex');
  select.addEventListener('change', function() {
    if (this.value === '') {
      this.style.backgroundImage = 'none';
    } else {
      const flag = this.options[this.selectedIndex].dataset.flag;
      this.style.backgroundImage = `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="16"><rect width="24" height="16" fill="${flag === 'vn' ? '%23DA251C' : '%23FFFFFF'}"/><path d="${flag === 'vn' ? 'M0 0h24v16H0zM0 8h24v8H0z' : ''}" fill="${flag === 'vn' ? '%23FF0' : ''}"/></svg>')`;
      this.style.backgroundSize = '24px 16px';
      this.style.backgroundRepeat = 'no-repeat';
      this.style.backgroundPosition = 'center';
      this.style.paddingLeft = '5px';
    }
  });
});